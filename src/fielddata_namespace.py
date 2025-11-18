from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef

class FieldDataNS(DefinedNamespace):

    _NS = Namespace("https://github.com/sylvainloiseau/rdfFieldData/")

    # Prefix for generating IRI
    URI_PREFIX_MediaSourceSet = 'MediaSourceSet-'
    URI_PREFIX_Event = "Event-"
    URI_PREFIX_FieldSession = "FieldSession-"
    URI_PREFIX_WrittenSource = 'WrittenSource-'
    URI_PREFIX_MediaReference = "MediaReference-"
    URI_PREFIX_Language = "Language-"
    URI_PREFIX_Person = "Person-"
    URI_PREFIX_Name = "Name-"
    URI_PREFIX_CREATIONRELATION = "CreationRelation-"
    URI_PREFIX_RoleType = "RoleType-"
    URI_PREFIX_WrittenSourcePaperInstantiation = "WrittenSourcePaperInstantiation-"
    URI_PREFIX_ContentType = "ContentType-"
    URI_PREFIX_RecordPhoto = "RecordPhoto-"
    URI_PREFIX_InstantiationPhoto = "InstantiationPhoto-"
    
    Missing = "Missing"

    EventType_Performance = "Performance"
    EventType_DataSession = "DataSession"
    
    FieldSessionEventType = "Field trip"


    # Entities
    Recording:URIRef
    MediaSourceSet:URIRef
    MediaSource:URIRef

    # Relation
    Transcription:URIRef
    Product:URIRef
    

    #Property
    
    FileName:URIRef # the basename
    ID:URIRef # ID of an Event or record

    Photo:URIRef
    Speaker:URIRef
    Consultant:URIRef
    MediaRef:URIRef
    FileName:URIRef
    NoteBookRef:URIRef
    qualifiedName:URIRef
    
    FieldSessionName:URIRef



