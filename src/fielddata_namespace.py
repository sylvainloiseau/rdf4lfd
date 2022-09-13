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

    Transcription:URIRef
    Product:URIRef
    Analyse:URIRef

    #Property
    URL:URIRef
    _NS = Namespace("https://github.com/sylvainloiseau/rdfFieldData#")

