from rdf4lfd.parse_directory import ConvertDirectoryIntoRicRdf
import os
from rdflib.namespace import RDF
from rdflib import URIRef
from rico_namespace import RICO
from test_SayMore import TestCommon

class TestConvertDirectoryIntoRicRdf:

    @staticmethod
    def test_parse_directory(request):
        directory = os.path.join(os.path.dirname(request.path), '../sample/data/SayMoreProjects/Test2/Sessions')
        parser = ConvertDirectoryIntoRicRdf(
            directory=directory,
            corpus_uri_prefix="http://mycorpus",
            extensions=[".MOV", ".WAV", ".MTS", ".wav", ".wma"],
            graph_identifier="directory",
            directoryhook=None,
            filesethook=None,
            filehook=None
        )
        parser.convert()
        g = parser.get_graph()
        x = len(g)

        print(len(g))
        g.bind("rico", RICO)
        g.bind("rdf", RDF)
        assert x == 29, TestCommon._printgraph(g)
        assert (URIRef("http://mycorpus/Event/Session1"), RDF.type, RICO.Event) in g, TestCommon._printgraph(g)