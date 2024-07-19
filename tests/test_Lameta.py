import pytest
from pickle import FALSE
import pytest
import xmltodict
from lameta_namespace import LametaNS
from parse_lameta import XmlDocument2rdfTriple, Lameta2RdfParser
from rdflib import Graph, Literal, URIRef, Namespace, BNode, Dataset
import os

class TestLameta:
    
    @pytest.mark.resources_creation
    def test_convert_Lameta(capsys, tmp_path, request):
        """
        This test will be runned only when pytest is called with the ```--create_resources``` option
        """
        destination_file = os.path.join(os.path.dirname(request.path), "../sample/data/rdf/from_Lameta/TuwariLameta.ttl")
        sm = Lameta2RdfParser("sample/data/LametaProjects/Test", "http://www.example.com")
        sm.convert()
        g:Graph = sm.get_graph()
        g.serialize(destination=destination_file, format="ttl")
        print("Conversion completed")

class TestCommon:

    @staticmethod
    def _printgraph(g:Graph):
        for s, p, o in g:
          print((s, p, o))

    @staticmethod
    def _printdatase(d:Dataset):
        for s, p, o, g in d:
          print((s, p, o, d))
          

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
        assert (None, LametaNS.parent, Literal("foo")) in g, TestCommon._printgraph(g)

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
        assert (None, LametaNS.xml, None) in g
        assert (None, LametaNS.f, Literal("text1")) in g

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
        assert (None, LametaNS.xml, None) in g, TestCommon._printgraph(g)
        assert (None, LametaNS.f, Literal("text1")) in g, TestCommon._printgraph(g)
        assert (URIRef("root/xml"), LametaNS['f/@attr'], Literal("val")) in g, TestCommon._printgraph(g)

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
        assert (None, LametaNS['xml'], None) in g
        assert (None, LametaNS['super'], None) in g
        assert (URIRef("root/xml/super"), LametaNS['sub1'], Literal("val1")) in g, TestCommon._printgraph(g)
        assert (URIRef("root/xml/super"), LametaNS['sub2'], Literal("val2")) in g, TestCommon._printgraph(g)


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
        assert (None, LametaNS['xml'], None) in g
        assert (None, LametaNS['super'], None) in g
        assert (URIRef("root/xml/super"), LametaNS['sub1'], Literal("val1")) in g, TestCommon._printgraph(g)
        assert (URIRef("root/xml/super"), LametaNS['sub1'], Literal("val2")) in g, TestCommon._printgraph(g)


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
        assert (None, LametaNS['xml'], None) in g
        assert (None, LametaNS['super'], None) in g
        assert (URIRef("root/xml/super"), LametaNS['sub1'], None) in g, TestCommon._printgraph(g)
        assert (URIRef("root/xml/super"), LametaNS['sub1'], None) in g, TestCommon._printgraph(g)
        assert (URIRef("root/xml/super/sub10"), LametaNS['x'], Literal("val1")) in g, TestCommon._printgraph(g)
        assert (URIRef("root/xml/super/sub11"), LametaNS['x'], Literal("val2")) in g, TestCommon._printgraph(g)

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
        assert (None, LametaNS['xml'], None) in g
        assert (None, LametaNS['f'], None) in g
        for s, p, o in g:
            if str(o) == "root/xml/f":
                assert isinstance(o, BNode)



