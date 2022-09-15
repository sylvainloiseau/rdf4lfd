import pytest
from pickle import FALSE
import pytest
import xmltodict
from rdf4lfd.parse_spreadsheet import Spreadsheet2RDF
from rdflib import Graph, Literal, URIRef, Namespace, BNode
import os

class TestSpreadsheet:

    @staticmethod
    def test_spreadsheet(request):
        context_graph_file = os.path.join(os.path.dirname(request.path), '../sample/data/rdf/from_SayMore/TuwariSayMore.ttl')
        #conf_file = os.path.join(os.path.dirname(request.path), '../sample/data/rdf/from_directory/Test2.turtle')
        destination_file = os.path.join(os.path.dirname(request.path), '../sample/data/rdf/from_spreadsheet_ods/Index.turtle')
        parser = Spreadsheet2RDF(
            file="sample/data/spreadsheet/ods/Index.ods",
            format="ODS",
            sheet_index=1,
            conf_file="sample/data/spreadsheet/conf/conf.json",
            context_graph_file=context_graph_file,
            corpus_uri_prefix = "http://tuwari.huma-num.fr/corpus/tuwari/#"
        )
        parser.convert()
        g = parser.get_graph()
        g.serialize(destination=destination_file)

