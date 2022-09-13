from rdflib.namespace import Namespace

class FieldDataNS(Namespace.ClosedNamespace):
    """
    Create predicate specific for linguistic fieldwork data:
    - Source : a document that can be analyzed
    - transcription : a relation between a Source and another source
    - product : a source that is produced during an activity
    - analyse : a relation between a source and a source produced during another activity
    """
    def __init__(self):
        super().__init__(self, "http://www.fieldworkdata.ns", ["transcription", "product", "analyse"])

