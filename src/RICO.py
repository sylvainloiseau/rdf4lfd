from rdflib import ClosedNamespace

class RIC(ClosedNamespace):
    ric_str = "https://www.ica.org/standards/RiC/ontology#"
    ric_terms = [
        "SubEvent",
        "Recording",
        "EventType",
        "Product",
        "Transcription",
        "Comment",
        "Mention",
        "Analyze",
        "Transcription",
        "Continuation",
        "Stimulus",
        "MentionInNotebook",
        "FieldSessionName",
        "Date",
        "Language",
        "Speaker",
        "Consultant",
        "Photo",
        "Title",
        "MediaSourceSet",
        "MediaRef",
        "MediaSource",
        "FileName",
        "DirName",
        "StartSpan",
        "EndSpan",
        "NoteBookRef (type)",
        "qualifiedName",
        "NotebookVol",
        "NotebookPage",
        "otherFlexComText"
    ]

    def __new__(cls):
        super().__new__(cls, RIC.ric_str, RIC.ric_terms)
