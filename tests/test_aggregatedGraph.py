from aggregatedGraph import AggregatedGraph, AggregateGraphNS
import os
from rdflib.namespace import RDF
from rdflib import URIRef, Literal
from tests.test_Lameta import TestCommon
from typing import List
import pytest

class TestAggregatedGraph:

    tiny_graphes = [
            ('../sample/data/rdf/from_directory/dir_tiny.turtle', 'directory'),
            ('../sample/data/rdf/from_Lameta/TuwariSayMore_tiny.ttl', 'lameta'),
            ('../sample/data/rdf/from_spreadsheet_ods/Index_tiny.ttl', 'spreadsheet')
        ]

    large_graphes = [
            ('../sample/data/rdf/from_directory/dir.turtle', 'directory'),
            ('../sample/data/rdf/from_Lameta/TuwariSayMore.ttl', 'lameta'),
            ('../sample/data/rdf/from_spreadsheet_ods/Index.ttl', 'spreadsheet')
        ]

    @pytest.mark.resources_creation
    def test_creating_aggretated_tiny(capsys, tmp_path, request):
        """
        This test will be runned only when pytest is called with the ```--create_resources``` option
        """
        destination_file = os.path.join(os.path.dirname(request.path), "../sample/data/rdf/aggregated/aggregated_tiny.nquads")
        ag = AggregatedGraph(destination_file, create=True)
        ag = TestAggregatedGraph._populate_aggr_graph(ag, request.path, TestAggregatedGraph.large_graphes)
        names = ag.get_subgraphes()
        assert len(names) == 5, names
        ag.save_database()
        
    @staticmethod
    def test_createGraph(capsys, tmp_path, request):
        destination_file = os.path.join(os.path.dirname(tmp_path), 'aggregated.ttl')
        ag = AggregatedGraph(destination_file, create=True)
        assert (AggregateGraphNS.Aggregated, AggregateGraphNS.name, Literal(destination_file), AggregateGraphNS._NS) in ag.database, TestCommon._printgraph(ag)
        ag.save_database()
        with pytest.raises(Exception):
            ag = AggregatedGraph(destination_file, create=True)

    def _populate_aggr_graph(ag:AggregatedGraph, prefix_path:str, graphes:List[str]) -> AggregatedGraph:
        for graphpath, graphname in graphes:
            ag.add_subgraph(str(os.path.join(os.path.dirname(prefix_path), graphpath)), graphname)
        return ag

    @staticmethod
    def test_get_subgraphes(capsys, tmp_path, request):
        destination_file = os.path.join(os.path.dirname(tmp_path), 'aggregated.ttl')
        ag = AggregatedGraph(destination_file, create=True)
        ag = TestAggregatedGraph._populate_aggr_graph(ag, request.path, TestAggregatedGraph.tiny_graphes)
        names = ag.get_subgraphes()
        assert len(names) == 5, names
        for n in names:
            print(f"-   {n}")
        with capsys.disabled():
            print(capsys.readouterr().out)

    @staticmethod
    def test_add_subgraph(capsys, tmp_path, request):
        destination_file = os.path.join(os.path.dirname(tmp_path), 'aggregated.ttl')
        ag = AggregatedGraph(destination_file, create=True)
        ag = TestAggregatedGraph._populate_aggr_graph(ag, request.path, TestAggregatedGraph.tiny_graphes)
        assert (len(ag.database) > 10), TestCommon._printdatase(ag.database)
        with capsys.disabled():
            print(f"{len(ag.database)} quads found")
        output = capsys.readouterr().out

    @staticmethod
    def test_update_subgraph(capsys, tmp_path, request):
        destination_file = os.path.join(os.path.dirname(tmp_path), 'aggregated.ttl')
        ag = AggregatedGraph(destination_file, create=True)
        with capsys.disabled():
            print("")
        with capsys.disabled():
            print(f"{len(ag.database)} quads found before adding")
        ag.add_subgraph(os.path.join(os.path.dirname(request.path), "../sample/data/rdf/from_SayMore/TuwariSayMore_tiny.ttl"), "lameta")
        with capsys.disabled():
            print(f"{len(ag.database)} quads found after adding")
        ag.update_subgraph("lameta")
        with capsys.disabled():
            print(f"{len(ag.database)} quads found after updating")

    # @staticmethod
    # def test_createGraph(request):
    #     directory = os.path.join(os.path.dirname(request.path), '../sample/data/SayMoreProjects/Test2/Sessions')
    #     parser = ConvertDirectoryIntoRicRdf(
    #         directory=directory,
    #         corpus_uri_prefix="http://mycorpus",
    #         extensions=[".MOV", ".WAV", ".MTS", ".wav", ".wma"],
    #         graph_identifier="directory",
    #         directoryhook=None,
    #         filesethook=None,
    #         filehook=None
    #     )
    #     parser.convert()
    #     g = parser.get_graph()
    #     x = len(g)

    #     print(len(g))
    #     g.bind("rico", RICO)
    #     g.bind("rdf", RDF)
    #     assert x == 29, TestCommon._printgraph(g)
    #     assert (URIRef("http://mycorpus/Event/Session1"), RDF.type, RICO.Event) in g, TestCommon._printgraph(g)