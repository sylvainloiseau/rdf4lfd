import xml.etree.ElementTree as ET
from pathlib import Path
import xmltodict
from rdflib import Graph, Literal, URIRef, Namespace, BNode
from rdflib.namespace import RDF, FOAF, ClosedNamespace
from collections.abc import Mapping
from collections import OrderedDict
from urllib.parse import quote_plus
from typing import Union
from abc import ABC, abstractmethod
import re
from rdf4lfd.rico_namespace import RICO
from rdf4lfd.lameta_namespace import LametaNS
from rdf4lfd.converter import Converter

class Lameta(object):

    PROJECT_META_SUFFIX = ".sprj"
    DESCRIPTION_DOCUMENTS_DIRNAME = "DescriptionDocuments"
    OTHER_DOCUMENTS_DIRNAME = "OtherDocuments"

class Lameta2RdfParser(Converter):
    """
    Convert a Lameta project into RDF.

    The file structure as well as the medata information provided are preserved
    for the different objects (projet, sessions, people).

    the RDF predicates are mainly the names of the XML elements of the SayMore/Lameta documents. Other predicates include:
    - FileUrl predicate for associating the actual URL of a document to its RDF node.
    - File predicate for linking a file to a Project, a Session or a Person node.
    - RDF.type

    """

    def __init__(self, project_dirname:str, corpus_uri_prefix:str):

        self.project_dir = Path(project_dirname)
        assert self.project_dir.is_dir(), "SayMore/Lameta projet path must be an existing directory"
        
        self.corpus_uri_prefix = corpus_uri_prefix
        self.projectname = self.project_dir.name
        self.projectfile = self.projectname + Lameta.PROJECT_META_SUFFIX
        self.graph = Graph(identifier=URIRef(project_dirname))
        self.graph.namespace_manager.bind('lameta', LametaNS, override=False)
        self.graph.namespace_manager.bind('rico', RICO, override=False)
        self.graph.namespace_manager.bind('mydata', corpus_uri_prefix, override=False)

    def convert(self):
        """
        Create a RDF graph holding all the metadata expressed in the SayMore/Lameta project
        """
        self.projectURIRef = URIRef(self.corpus_uri_prefix + "/project/" + self.projectname)

        # Add data in the project metadata doc
        self.parseProjectDoc()

        # Add data in "Sessions" directory
        LametaSessionsDirectory(self).read()

        # Add data in "People" directory
        LametaPeopleDirectory(self).read()

        # Add document in "DescriptionDocuments" directory
        self.addSupplementaryDirectory(self.project_dir / Lameta.DESCRIPTION_DOCUMENTS_DIRNAME, "DescriptionDocument")

        # Add document in "OtherDocuments" directory
        self.addSupplementaryDirectory(self.project_dir / Lameta.OTHER_DOCUMENTS_DIRNAME, "OtherDocument")


    def get_graph(self) -> Graph:
        return self.graph

    def addSupplementaryDirectory(self, directory, predicate):
        p = Path(directory)
        if p.exists():
            for f in p.iterdir():
                if f.is_file():
                    self.graph.add((URIRef(self.projectURIRef), LametaNS[predicate], Literal(str(f))))

    def parseProjectDoc(self):
        XmlDocument2rdfTriple.parse(self.project_dir / self.projectfile, self.projectURIRef, self.graph)
        self.graph.add((self.projectURIRef, RDF.type, LametaNS.Project))

class AbstractLametaDirectoryList(ABC):

    def __init__(self, project:Lameta2RdfParser):
        self.project = project

    def read(self):
        self.project.graph.add((self.project.projectURIRef, LametaNS[self.directory], URIRef(self.project.corpus_uri_prefix + "/" + self.directory)))
        self._walkLametaDirectoryList()

    @abstractmethod
    def metaDocumentReader(self, file_path, uri):
        pass

    def _walkLametaDirectoryList(self):
        """
        Walk through a list of directories (such as the various sessions, or the various person) and,
        for each directory, populate the graph with the metadata (about a session or a person)
        and the metadata associated with each files contained in the directories.
        """

        parent_fullpath = self.project.project_dir / self.directory
        
        for i, objectdir in enumerate(Path(parent_fullpath).iterdir()):
            if str(objectdir) == str(parent_fullpath):
                continue
            object_name = objectdir.name
            object_URIRef = URIRef(self.project.corpus_uri_prefix + "/" + self.directory + "/" + quote_plus(object_name))
            self.project.graph.add((URIRef(self.project.corpus_uri_prefix + "/" + self.directory), LametaNS[self.predicate], object_URIRef ))
            object_metafile_fullpath = objectdir / (object_name + self.extension)
            # Read the document describing the Session or the Person
            self.metaDocumentReader(object_metafile_fullpath, object_URIRef)
            ReadDirectoryContent._readDirectory(objectdir, object_URIRef, self.project.graph)

class LametaSessionsDirectory(AbstractLametaDirectoryList):
    """The Sessions directory, which contains a set of subdirectory for each session"""

    def __init__(self, project:Lameta2RdfParser):
        super().__init__(project)
        # TODO rendre static
        self.directory = "Sessions"
        self.extension = ".session"
        self.predicate = "Session"

    def metaDocumentReader(self, file_path:Path, uri:URIRef):
        """ parse a document holding meta information about a session in a session directory"""
        XmlDocument2rdfTriple.parse(file_path, uri, self.project.graph)
        self.project.graph.add((uri, RDF.type, LametaNS[self.predicate]))
        # TODO change predicate or object value if needed

class LametaPeopleDirectory(AbstractLametaDirectoryList):
    """The People directory, which contains a set of subdirectory for each person"""
    def __init__(self, project:Lameta2RdfParser):
        super().__init__(project)
        # TODO rendre static
        self.directory = "People"
        self.extension = ".person"
        self.predicate = "People"

    def metaDocumentReader(self, file_path:Path, uri):
        """ parse a document holding meta information about a person in a person directory"""
        g = Graph()
        XmlDocument2rdfTriple.parse(file_path, uri, g)
        # TODO change predicate or object value if needed
        self.project.graph = self.project.graph + g
        self.project.graph.add((URIRef(uri), RDF.type, LametaNS[self.predicate]))

class ReadDirectoryContent():
    """
    Read the documents in a directory, each document "d" has a paired file "d.meta"
    """

    @staticmethod
    def parseAdditionalDocumentMetaDoc(file_path:Path, documentURI:URIRef, graph:Graph):
        XmlDocument2rdfTriple.parse(file_path, documentURI, graph)

    @staticmethod
    def _readDirectory(d:Path, parent_uri:URIRef, graph):
        for f in d.iterdir():
            if not f.is_file(): raise Exception(f"{f} is not a regular file in {d}")
            if f.suffix == ".meta":
                mediaFileFullpath = f.with_suffix("")
                mediaSuffix       = mediaFileFullpath.suffix
                mediaFileBasename = mediaFileFullpath.name

                fileURIRef = URIRef(parent_uri + "/" + quote_plus(mediaFileBasename))

                # Lameta offer to use a suffixe in the basename to distinguish various kind of files of a session (Source, Transcription...)
                # This suffix is preserved in a LametaNamespace.FileType predicate
                pattern = d.name + "_(.+)" + mediaSuffix
                res = re.search(pattern, mediaFileBasename)
                if res:
                    graph.add((fileURIRef, LametaNS.FileType, Literal(res.group(1))))

                # Create a link between the parent node (a session, a person, or the additional document dir) and this file description
                graph.add((parent_uri, LametaNS.File, fileURIRef))
                graph.add((fileURIRef, RDF.type, LametaNS.File))

                # Create a link between the file description and the actual URL of the file
                graph.add((fileURIRef, LametaNS.FileUrl, Literal(mediaFileFullpath)))
                ReadDirectoryContent.parseAdditionalDocumentMetaDoc(f, fileURIRef, graph)

class XmlDocument2rdfTriple():
    """
    Convert an XML document into RDF triple, using Litteral for text node and attribute value, and using
    URIRef for reflection XML tree hierarchy. When several element with the same name are children of a parent
    element, the URIRef are suffixed with a number.
    """

    @staticmethod
    def parse(file_P:Path, root_URIRef:URIRef, graph:Graph):
        document = file_P.read_text()
        d = xmltodict.parse(document)
        rootElements = list(d.keys())
        assert len(rootElements) == 1, "xml-backed dictionary must have one top-level entry"
        XmlDocument2rdfTriple._dictionary2triple(root_URIRef, d[rootElements[0]], graph)

    @staticmethod
    def _dictionary2triple(rootURIRef:URIRef, dictionary:Mapping, graph:Graph) -> None:
        """
        Recursively populate an RDF graph with a dictionary. Dictionary values can be one of:
        - a string. In this case, a triplet (rootURI, key, value) is injected
        - a dictionary. In this case, a triplet (rootURI, key, ValueURI) is created, and the
          function is recursively called with ValueURI as root and the inner dictionary as dictionary.
        - a list of values. In this case, all values yield in a (root, key, valueN) triplet. If one
        of the value is a dictionary, the function is recursively called as above.

        A special case of dictionary is a dictionary containing a key "#text"
        with all other key starting with "@". In that case, no recursive call is done.


        >>> xmltodict.parse("<xml><f attr='val'>text1</f></xml>")
        OrderedDict([('xml', OrderedDict([('f', OrderedDict([('@attr', 'val'), ('#text', 'text1')]))]))])

        """
        assert isinstance(rootURIRef, URIRef)
        if (dictionary is None):
            return graph
        for k,v in dictionary.items():
            if isinstance(v, Mapping):
                XmlDocument2rdfTriple._selectMappingKind(rootURIRef, v, graph, k, "")
            elif isinstance(v, list):
                for i, e in enumerate(v):
                    if isinstance(e, Mapping):
                        XmlDocument2rdfTriple._selectMappingKind(rootURIRef, e, graph, k, str(i))
                    else:
                        graph.add((rootURIRef, LametaNS[k], Literal(e)))
            else:
                XmlDocument2rdfTriple._add_secure(graph, rootURIRef, LametaNS[k], v)

    @staticmethod
    def _selectMappingKind(rootURIRef:URIRef, m:Mapping, graph:Graph, parentKey:str, rankInParentKey:str):
        """
        When a Mapping is found as a value in _dictionary2triple, choose between:
        - a Mapping containing node text and attribute of an element, to be injected directly
        - a Mapping containing new key/value pair, to be injected through the creation of a parent node and a recursive call to _dictionary2triple.
        """
        nm = OrderedDict()
        for k2, v2 in m.items():
            if k2 == "#text":
                # should not be empty according to test of xmltodict
                graph.add((rootURIRef, LametaNS[parentKey], Literal(v2)))
            elif k2.startswith("@"):
                if k2 == "@type":
                    pass
                else:
                    XmlDocument2rdfTriple._add_secure(graph, rootURIRef, LametaNS[parentKey + "/" + k2], v2)
            else:
                nm[k2] = v2
        if len(nm) > 0:
            # FIXME check: rootURIRef + "/" + parentKey  or rootURIRef?
            newrootURI = URIRef(rootURIRef + "/" + parentKey + quote_plus(rankInParentKey))
            graph.add((rootURIRef, LametaNS[parentKey], newrootURI))
            XmlDocument2rdfTriple._dictionary2triple(newrootURI, nm, graph)

    @staticmethod
    def _add_secure(graph:Graph, subject:URIRef, predicate:URIRef, obj:Union[str, None]) -> None:
        obj = BNode() if obj == None else Literal(obj)
        graph.add((subject, predicate, obj))

class Lameta2RicO(object):
    """
    Utilities for converting a SIL SayMore/Lameta repository into an RDF graph
    """

    def __init__(self, graph):
        self.graph = graph

    def run(self):
        self._change_type()
        self._change_Person_properties()
        self._change_language()
        #self._applySparql(self._add_rico_ontology_query)
        #self._applySparql(self._add_rico_ontology_query2)


    def get_graph(self):
        return self.graph

    def _applySparql(self, query):
        self.graph.update(query, initNs={
            'rdf':'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'lameta':'https://github.com/onset/lameta/',
            'rico':'https://www.ica.org/standards/RiC/ontology/2.0/'})

    def _change_type(self):
        types = [
            ("People", "Person"),
            ("Project", "RecordSet"),
            ("Session", "Event"),
            ("File", "Instantiation")
        ]
        for old, new in types:
            q = f'DELETE {{ ?person a lameta:{old} }} INSERT {{ ?person a rico:{new}. }} WHERE  {{ ?person a lameta:{old}. }}'
            self._applySparql(q)

    def _change_Person_properties(self):
        properties = [
                ('birthYear', 'date'),
                ('primaryLanguage', 'hasOrHadLanguage'),
                ('otherLanguage0', 'hasOrHadLanguage'),
                ('otherLanguage1', 'hasOrHadLanguage'),
                ('name', 'name'),
                ('code', 'identifier'),
                ('description', 'generalDescription'),
                ('notes', 'note')
        ]
        for old, new in properties:
            q = f"  DELETE {{ ?person lameta:{old} o2 }} INSERT {{ ?person rico:{new} o2. }} WHERE  {{ ?person a rico:Person ; ?person lameta:{old} o2. }}"
            self._applySparql(q)

   # introduce a Language object into the link between a Person and a language litteral
    def _change_language(self):
        self._applySparql(f'DELETE {{ ?person rico:hasOrHadLanguage o2 }} INSERT {{ ?person rico:hasOrHadLanguage ?lang_uri; ?lang_uri a rico:Language; ?lang_uri rico:name o2. }} WHERE  {{ ?person a rico:Person ; ?person rico:hasOrHadLanguage o2. BIND(URI(CONCAT("languages/", MD5(STR(?o2)))) as ?lang_uri)}}')

    # gender
    # education
    # ethnicGroup
    # fathersLanguage
    # howToContact
    # mothersLanguage
    # nickName
    # primaryLanguage
    # primaryLanguageLearnedIn
    # primaryOccupation

    # https://stackoverflow.com/questions/19502398/sparql-update-example-for-updating-more-than-one-triple-in-a-single-query
    _add_rico_ontology_query2 = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX lameta: <https://github.com/onset/lameta/> 
        PREFIX rico: <https://www.ica.org/standards/RiC/ontology/2.0/> 

        DELETE {?s ?p ?o}
        INSERT {?s rdf:type rico:People ;
                ex:description "bar" ;
                rdf:type ex:FooBar .  
            }
        WHERE  { ?s ?p ?o . 
                FILTER (?o = lameta:People) 
        }""" 

    

    def linkSessionToPeopleNode(self, g:Graph):
        # When session have contributor(s), replace the name of the contributor
        # with a link to the FOAF.person node defining that person
        q = """
        DELETE { ?c ns1:name ?name }
        INSERT { ?c ns1:contributorURI ?contributor }
        WHERE
          { ?contributors ns1:contributor ?contributor
            ?contributor ns1:name ?name
            ?session a ns1:session
            ?session ns1:contributions ?cs
            ?cs ns1:contributor ?c
            ?c ns1:name ?name
          }
        """
        self._applySparql(q)

    def addInformationByFilePattern(self, sameShot="", sameDevice="", sameChannel=""):
        """
        {
          {
            pattern:""
            predicate:""
            value:""
          }
        }
        """

    def addFileMetadata(self):
        pass

    def organiseMediaFile(self):
        """ recognise session, etc."""
        pass

    def typeValue(self):
        qs = [
        """
        DELETE { ?c a ns1:Person }
        INSERT { ?c a FOAF:Person }
        WHERE
          { ?c ns1:Person ?p
          }
        """,
        """
        DELETE { ?c a ns1:Session }
        INSERT { ?c a RiC:Event }
        WHERE
          { ?c ns1:Session ?p
          }
        """,
        """
        """
        ]
# rajouter type :
# - sur personne : rajouter foaf:Person
# - sur Recording : RiC:xxxx
# - sur session : RiC:Event/Activity
# remplacer les actuelles valeurs du prédicat RDF.type
#
# record the path of an event / people as a property
# parse file name (prefix=session/suffix)
        pass

    def removeBlankNode():
        pass

