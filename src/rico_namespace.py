from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef
from owlready2 import get_ontology, World
import os
import sys

class Owl2UriRef():
    def __init__(self):
        pkg_d = os.path.dirname(sys.modules[__name__].__file__)
        ricopath = "file://" + os.path.join(pkg_d, "ontologies/RiC-O_1-0-2.rdf")

        self.world = World()
        self.onto = self.world.get_ontology(ricopath).load()

    def get(self, symbol:str):
        return RICO[str(self.onto[symbol])]

class RicoOwl():
    """
    For testing purposes
    """

    def __init__(self):
        pkg_d = os.path.dirname(sys.modules[__name__].__file__)
        ricopath = "file://" + os.path.join(pkg_d, "ontologies/RiC-O_1-0-2.rdf")
        self.onto = get_ontology(ricopath).load()

    def get_iri(self):
        return self.onto.base_iri
    
    def get_classes(self):
        classes = self.onto.classes()
        return classes

class RICO(DefinedNamespace):
    _NS = Namespace("https://www.ica.org/standards/RiC/ontology/2.0/")

    # relation
    hasOrHadName:URIRef
    hasInstance:URIRef
    documentedBy:URIRef
    note:URIRef
    hasContentOfType:URIRef
    hasInstantiation:URIRef
    hasPart:URIRef
    roleIsContextOfCreationRelation:URIRef
    relationHasSource:URIRef
    relationHasTarget:URIRef
    hasOrHadLanguage:URIRef
    precedesInTime:URIRef
    name:URIRef

    # entity
    Record:URIRef
    Event:URIRef
    Instantiation:URIRef
    SubEvent:URIRef
    ContentType:URIRef
    Name:URIRef
    RecordSet:URIRef
    CreationRelation:URIRef
    RoleType:URIRef

    # Property
    EventType:URIRef
    Date:URIRef
    Language:URIRef
    Title:URIRef
    Person:URIRef
    _pytestfixturefunction:URIRef
