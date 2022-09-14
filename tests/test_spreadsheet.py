import pytest
from pickle import FALSE
import pytest
import xmltodict
#from rdffielddata import SayMore2RdfParser, XmlDocument2rdfTriple
from spreadsheet import CSV2RDF
#from saymore import SayMore2RdfParser, XmlDocument2rdfTriple
from rdflib import Graph, Literal, URIRef, Namespace, BNode
import os

class TestCsv:

    @staticmethod
    def test_csv():
        parser = CSV2RDF(
            file="sample/data/spreadsheet/ods/Index.ods",
            format="ODS",
            sheet_index=1,
            conf_file="sample/data/spreadsheet/conf/conf.json",
            context_graph=None,
            corpus_uri_prefix = "http://tuwari.huma-num.fr/corpus/tuwari/#"
        )
        parser.convert()

