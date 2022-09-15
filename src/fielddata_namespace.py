from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef

class FieldDataNS(DefinedNamespace):
    """
    Create predicate specific for linguistic fieldwork data:
    - Source : a document that can be analyzed
    - transcription : a relation between a Source and another source
    - product : a source that is produced during an activity
    - analyse : a relation between a source and a source produced during another activity
    """
 
    # Prefix for generating IRI
    URI_PREFIX_MediaSourceSet = 'MediaSourceSet-'
    URI_PREFIX_Event = "Event-"
    URI_PREFIX_FieldSession = "FieldSession-"
    URI_PREFIX_WrittenSource = 'WrittenSource-'
    URI_PREFIX_MediaReference = "MediaReference-"
    Missing = "Missing"

    FieldSessionEventType = "FieldSession"

    # Entities
    Recording:URIRef
    MediaSourceSet:URIRef
    MediaSource:URIRef

    # Relation
    Transcription:URIRef
    Product:URIRef
    Analyse:URIRef
    MentionInNotebook:URIRef

    #Property
    URL:URIRef
    FileName:URIRef # the basename
    ID:URIRef # ID of an Event or record

    Photo:URIRef
    Speaker:URIRef
    Consultant:URIRef
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
    FieldSessionName:URIRef


    _NS = Namespace("https://github.com/sylvainloiseau/rdfFieldData/")

