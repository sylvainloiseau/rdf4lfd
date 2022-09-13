from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef

class RICO(DefinedNamespace):
    _NS = Namespace("https://www.ica.org/standards/RiC/ontology#")

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
    SubEvent:URIRef
    Recording:URIRef
    MediaSourceSet:URIRef
    MediaSource:URIRef

    # Property
    EventType:URIRef
    MentionInNotebook:URIRef
    FieldSessionName:URIRef
    Date:URIRef
    Language:URIRef
    Speaker:URIRef
    Consultant:URIRef
    Photo:URIRef
    Title:URIRef
    MediaRef:URIRef
    FileName:URIRef
    DirName:URIRef
    StartSpan:URIRef
    EndSpan:URIRef
    NoteBookRef:URIRef
    qualifiedName:URIRef
    NotebookVol:URIRef
    NotebookPage:URIRef
    otherFlexComText:URIRef
