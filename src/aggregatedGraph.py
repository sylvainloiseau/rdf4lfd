from pathlib import Path
from rdflib import Graph, Literal, URIRef, Namespace, BNode, Dataset
from rdflib.namespace import RDF, FOAF, ClosedNamespace
from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef, Node
from urllib.parse import quote_plus
from typing import Union, List
from rdf4lfd.fielddata_namespace import FieldDataNS
from datetime import datetime

class AggregatedGraph(object):

    """
    An RDF Graph (Quad) containing several aggregated data sources (subgraph)
    """

    def __init__(self, filename:str, create:bool=False):
        """
        :param create: 
        """
        self.filename = filename
        self.database = Dataset()
        if create:
            if (Path(filename).exists()):
                raise Exception(f"File already exists: {filename}")
            self._init_database()
        else:
            if (not Path(filename).exists()):
                raise Exception(f"File does not exist: {filename}")
            self.database.parse(filename,
                                publicID=AggregateGraphNS.database_publicID,
                                format="nquads")

    def get_subgraphes(self) -> List[str]:
        return [*self.database.graphs()]

    def add_subgraph(self, subgraph_uri:str, identifier:str) -> None:
        g = self.database.graph(identifier=identifier)
        self._subgraph_populate(g, subgraph_uri, identifier)

        self.database.add((URIRef(identifier), AggregateGraphNS.added, Literal(datetime.now()), AggregateGraphNS._NS))
        self.database.add((URIRef(identifier), AggregateGraphNS.filename, Literal(subgraph_uri), AggregateGraphNS._NS))

    def _subgraph_populate(self, g:Graph, filename:str, identifier:str) -> None:
        g.remove((None,None,None))
        g.parse(publicID=identifier, source=filename)
        for s,p,o in g:
            self.database.add((s,p,o,g))

    def update_subgraph(self, identifier) -> None:
        config_graph = self.database.graph(AggregateGraphNS._NS)
        filename_node:Node = config_graph.value(subject=URIRef(identifier), predicate=AggregateGraphNS.filename, object=None)
        filename = filename_node.value
        subgraph = self.database.graph(URIRef(identifier))
        
        self._subgraph_populate(subgraph, filename, identifier)

        self.database.add((URIRef(identifier), AggregateGraphNS.updated, Literal(datetime.now()), AggregateGraphNS._NS))

    def save_database(self):
        self.database.serialize(destination=self.filename, format="nquads")

    def _init_database(self):
        self.database.graph(identifier=AggregateGraphNS._NS)
        self.database.add((AggregateGraphNS.Aggregated, AggregateGraphNS.name,    Literal(self.filename),  AggregateGraphNS._NS))
        self.database.add((AggregateGraphNS.Aggregated, AggregateGraphNS.created, Literal(datetime.now()), AggregateGraphNS._NS))
class AggregateGraphNS(DefinedNamespace):
    """
    """
 
    # Entities
    Aggregated:URIRef

    # Relation
    name:URIRef
    added:URIRef
    updated:URIRef

    #Property
    URL:URIRef
    FileName:URIRef # the basename
    ID:URIRef # ID of an Event or record
    _pytestfixturefunction:URIRef

    database_publicID = "https://github.com/sylvainloiseau/aggregatedgraph_base"

    _NS = Namespace("https://github.com/sylvainloiseau/aggregatedgraph/")

