from parse_directory import ConvertDirectoryIntoRicRdf
import os
from rdflib.namespace import RDF
from rdflib import URIRef
from rico_namespace import RICO
from test_Lameta import TestCommon
import pytest

class TestConvertDirectoryIntoRicRdf:

    @staticmethod
    @pytest.mark.resources_creation
    def test_parse_directory(request):
        directory = os.path.join(os.path.dirname(request.path), '../sample/data/LametaProjects/Test2/Sessions')
        format_and_extension = "trig"
        destination_file = os.path.join(os.path.dirname(request.path), '../sample/data/rdf/from_directory/test_parse_directory.' + format_and_extension)
        parser = ConvertDirectoryIntoRicRdf(
            directory=directory,
            corpus_uri_prefix="http://mycorpus.com",
            extensions=[".MOV", ".WAV", ".MTS", ".wav", ".wma"],
            graph_identifier="my_corpus_graph",
            directoryhook=None,
            filesethook=None,
            filehook=None
        )
        parser.convert()
        g = parser.get_graph()
        g.serialize(destination=destination_file, format=format_and_extension)
        x = len(g)

        print(len(g))
        g.bind("rico", RICO)
        g.bind("rdf", RDF)
        assert x == 26, TestCommon._printgraph(g)
        assert (URIRef("http://mycorpus.com/Event/Session1"), RDF.type, RICO.Event) in g, TestCommon._printgraph(g)