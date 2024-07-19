import pytest
from pickle import FALSE
import pytest
import xmltodict
from parse_spreadsheet import Spreadsheet2RDF
from rdflib import Graph, Literal, URIRef, Namespace, BNode
import os

class TestSpreadsheet:

    @pytest.mark.resources_creation
    def test_spreadsheet_create_resource(capsys, tmp_path, request):
        out = os.path.join(os.path.dirname(request.path), '../sample/data/rdf/from_spreadsheet_ods/Index.ttl')
        TestSpreadsheet._run_spreadsheet(out, request)

    def test_spreadsheet(capsys, tmp_path, request):
        out = os.path.join(os.path.dirname(tmp_path), 'spreadsheet.ttl')
        TestSpreadsheet._run_spreadsheet(out, request)

    def _run_spreadsheet(out, request):
        context_graph_file = os.path.join(os.path.dirname(request.path), '../sample/data/rdf/from_SayMore/TuwariSayMore.ttl')
        destination_file = out
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

