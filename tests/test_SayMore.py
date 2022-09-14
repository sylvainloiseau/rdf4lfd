import pytest
from pickle import FALSE
import pytest
import xmltodict
from rdffielddata.parse_saymore import XmlDocument2rdfTriple, SayMore2RdfParser
from rdflib import Graph, Literal, URIRef, Namespace, BNode
import os

class TestCommon:

    @staticmethod
    def _printgraph(g:Graph):
        for s, p, o in g:
          print((s, p, o))

class TestXmlDocument2rdfTriple:

    @staticmethod
    def test_add_secure_BNode():
        g = Graph()
        XmlDocument2rdfTriple._add_secure(g, URIRef("Subjecttest"), URIRef("PredicateTest"), None)
        for s, p, o in g:
            assert isinstance(o, BNode)

    @staticmethod
    def test_add_secure_String():
        g = Graph()
        XmlDocument2rdfTriple._add_secure(g, URIRef("Subjecttest"), URIRef("PredicateTest"), "foo")
        assert (None, None, Literal("foo")) in g

class TestSelectMappingKind:

    @staticmethod
    def test_selectMappingKind():
        g = Graph()
        root = URIRef("root")
        d = {"#text": "foo", "@attr1": "attr1value", "@attr2": "attr2value"}
        XmlDocument2rdfTriple._selectMappingKind(root, d, g, "parent", "")
        assert len(g) == 3
        assert (None, SayMore2RdfParser.rdfSayMoreNS['parent'], Literal("foo")) in g, TestCommon._printgraph(g)

class TestDictionary2Triple:

    serialize = True
    serialize_dir = "target/tests/"

    @staticmethod
    def test_dictionary2triple_Text():
        doc = """<xml><f>text1</f></xml>"""
        d = xmltodict.parse(doc)
        g = Graph()
        XmlDocument2rdfTriple._dictionary2triple(URIRef("root"), d, g)
        assert len(g) == 2
        assert (None, SayMore2RdfParser.rdfSayMoreNS['xml'], None) in g
        assert (None, SayMore2RdfParser.rdfSayMoreNS['f'], Literal("text1")) in g

    @staticmethod
    def test_dictionary2tripleAttr(tmp_path):
        doc = """<xml><f attr='val'>text1</f></xml>"""
        d = xmltodict.parse(doc)
        g = Graph()
        XmlDocument2rdfTriple._dictionary2triple(URIRef("root"), d, g)
        if TestDictionary2Triple.serialize:
          target_output = os.path.join(tmp_path,'dictionary2tripleAttr.ttl')
          g.serialize(destination = target_output)
        assert len(g) == 3
        assert (None, SayMore2RdfParser.rdfSayMoreNS['xml'], None) in g, TestCommon._printgraph(g)
        assert (None, SayMore2RdfParser.rdfSayMoreNS['f'], Literal("text1")) in g, TestCommon._printgraph(g)
        assert (URIRef("root/xml"), SayMore2RdfParser.rdfSayMoreNS['f/@attr'], Literal("val")) in g, TestCommon._printgraph(g)

    @staticmethod
    def test_dictionary2triple_InnerMap():
        doc = """
        <xml>
          <super>
            <sub1>val1</sub1>
            <sub2>val2</sub2>
          </super>
        </xml>
        """
        d = xmltodict.parse(doc)
        g = Graph()
        XmlDocument2rdfTriple._dictionary2triple(URIRef("root"), d, g)
        assert len(g) == 4
        assert (None, SayMore2RdfParser.rdfSayMoreNS['xml'], None) in g
        assert (None, SayMore2RdfParser.rdfSayMoreNS['super'], None) in g
        assert (URIRef("root/xml/super"), SayMore2RdfParser.rdfSayMoreNS['sub1'], Literal("val1")) in g, TestCommon._printgraph(g)
        assert (URIRef("root/xml/super"), SayMore2RdfParser.rdfSayMoreNS['sub2'], Literal("val2")) in g, TestCommon._printgraph(g)


    @staticmethod
    def test_dictionary2IndexedArray():
        d = xmltodict.parse("<xml><f attr='val'>text1</f><f attr='val2'>text2</f></xml>")
        # >>> d
        # OrderedDict([('xml', OrderedDict([('f', [OrderedDict([('@attr', 'val'), ('#text', 'text1')]), OrderedDict([('@attr', 'val2'), ('#text', 'text2')])])]))])
        g = Graph()
        XmlDocument2rdfTriple._dictionary2triple(URIRef("root"), d, g)
        assert len(g) == 5, TestCommon._printgraph(g)


    @staticmethod
    def test_dictionary2tripleArrayOfText(tmp_path):
        """ Two children with the same name: "sub1" and including only text node"""
        doc = """
        <xml>
          <super>
            <sub1>val1</sub1>
            <sub1>val2</sub1>
          </super>
        </xml>
        """
        d = xmltodict.parse(doc)
        g = Graph()
        XmlDocument2rdfTriple._dictionary2triple(URIRef("root"), d, g)
        assert len(g) == 4, TestCommon._printgraph(g)
        if TestDictionary2Triple.serialize:
          target_output = os.path.join(tmp_path,'dictionary2tripleArrayOfText.ttl')
          g.serialize(destination = target_output)
        assert (None, SayMore2RdfParser.rdfSayMoreNS['xml'], None) in g
        assert (None, SayMore2RdfParser.rdfSayMoreNS['super'], None) in g
        assert (URIRef("root/xml/super"), SayMore2RdfParser.rdfSayMoreNS['sub1'], Literal("val1")) in g, TestCommon._printgraph(g)
        assert (URIRef("root/xml/super"), SayMore2RdfParser.rdfSayMoreNS['sub1'], Literal("val2")) in g, TestCommon._printgraph(g)


    @staticmethod
    def test_dictionary2tripleArrayOfText2(tmp_path):
        """
        Two children with the same name and having each a sub-system: the node have to be distinguished by adding a number
        Otherwise, -[x]->(val1) and -[x]->(val2) would have the same subject, while they are related to two different subjects.
        Hence "sub10" and "sub11"
        """
        doc = """
        <xml>
          <super>
            <sub1><x>val1</x></sub1>
            <sub1><x>val2</x></sub1>
          </super>
        </xml>
        """
        d = xmltodict.parse(doc)
        g = Graph()
        XmlDocument2rdfTriple._dictionary2triple(URIRef("root"), d, g)
        assert len(g) == 6, TestCommon._printgraph(g)
        if TestDictionary2Triple.serialize:
          target_output = os.path.join(tmp_path,'dictionary2tripleArrayOfText2.ttl')
          g.serialize(destination = target_output)
        assert (None, SayMore2RdfParser.rdfSayMoreNS['xml'], None) in g
        assert (None, SayMore2RdfParser.rdfSayMoreNS['super'], None) in g
        assert (URIRef("root/xml/super"), SayMore2RdfParser.rdfSayMoreNS['sub1'], None) in g, TestCommon._printgraph(g)
        assert (URIRef("root/xml/super"), SayMore2RdfParser.rdfSayMoreNS['sub1'], None) in g, TestCommon._printgraph(g)
        assert (URIRef("root/xml/super/sub10"), SayMore2RdfParser.rdfSayMoreNS['x'], Literal("val1")) in g, TestCommon._printgraph(g)
        assert (URIRef("root/xml/super/sub11"), SayMore2RdfParser.rdfSayMoreNS['x'], Literal("val2")) in g, TestCommon._printgraph(g)

    @staticmethod
    def test_dictionary2tripleEmptyTextNode(tmp_path):
        doc = """<xml><f/></xml>"""
        d = xmltodict.parse(doc)
        g = Graph()
        XmlDocument2rdfTriple._dictionary2triple(URIRef("root"), d, g)
        assert len(g) == 2
        if TestDictionary2Triple.serialize:
          target_output = os.path.join(tmp_path,'dictionary2tripleEmptyTextNode.ttl')
          g.serialize(destination = target_output)
        assert (None, SayMore2RdfParser.rdfSayMoreNS['xml'], None) in g
        assert (None, SayMore2RdfParser.rdfSayMoreNS['f'], None) in g
        for s, p, o in g:
            if str(o) == "root/xml/f":
                assert isinstance(o, BNode)



