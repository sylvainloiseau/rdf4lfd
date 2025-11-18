from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef

class LinguisticFieldDataNS(DefinedNamespace):
    """
    Create predicate specific for linguistic fieldwork data:
    - Source : a document that can be analyzed
    - transcription : a relation between a Source and another source
    - product : a source that is produced during an activity
    - analyse : a relation between a source and a source produced during another activity
    """

    _NS = Namespace("https://lacito.cnrs.fr/linguisticFieldData#")

    Analyse:URIRef
    Stimulus:URIRef
    Mention:URIRef
    MentionInNotebook:URIRef
    URL:URIRef
    EventSubType:URIRef

    MentionInNotebook:URIRef

    SpanStartTimeStamp:URIRef
    SpanEndTimeStamp:URIRef
    
    NotebookVol:URIRef
    NotebookPage:URIRef
    otherFlexComText:URIRef