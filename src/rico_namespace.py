from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef

class RICO(DefinedNamespace):
    _NS = Namespace("https://www.ica.org/standards/RiC/ontology/2.0/")

    # relation
    hasInstance:URIRef
    Product:URIRef
    Transcription:URIRef
    Comment:URIRef
    Mention:URIRef
    Analyze:URIRef
    Transcription:URIRef
    Continuation:URIRef
    Stimulus:URIRef
    documents:URIRef

    # entity
    Record:URIRef
    Event:URIRef
    Instance:URIRef
    SubEvent:URIRef

    # Property
    EventType:URIRef
    Date:URIRef
    Language:URIRef
    Title:URIRef
    Person:URIRef
