from abc import abstractclassmethod
from logging import raiseExceptions
import os
import re
from typing import List
from abc import abstractmethod
from rdflib import Graph, URIRef, RDF, Literal
from rdf4lfd.rico_namespace import RICO
from rdf4lfd.fielddata_namespace import FieldDataNS
from rdf4lfd.converter import Converter
from urllib.parse import quote_plus

class DirectoryHook():
    @abstractclassmethod
    def directory_hook(g:Graph, event_node: URIRef, directory:str) -> None:
        pass

class FileHook():
    @abstractclassmethod
    def file_hook(g:Graph, record_node: URIRef, filenames:str) -> None:
        pass

class FilesetHook():
    @abstractclassmethod
    def fileset_hook(filenames:List[str]) -> List:
        pass

class ConvertDirectoryIntoRicRdf(Converter):
    """
    convert a directory into a set of Event containing Record (RICO RDF) where each subdirectory is a session and its content files are records.

    Event names are subdirectory names.

    If your directory is a SayMore/lameta directory, consider using the saymore module instead.
    """
    def __init__(self, 
        directory:str,
        corpus_uri_prefix: str,
        extensions:List[str] = None,
        graph_identifier=None,
        directoryhook:DirectoryHook=None,
        filesethook:FilesetHook=None,
        filehook:FileHook=None
    ):
        self.corpus_uri_prefix=corpus_uri_prefix

        if not os.path.isdir(directory):
            raise Exception(f"Not a directory: {directory}")
        self.directory=directory

        self.extensions=extensions
        if graph_identifier is None:
            graph_identifier = directory
        self.g = Graph(identifier=Literal(graph_identifier))

        self.directoryhook = directoryhook if directoryhook is not None else None
        self.filesethook = filesethook if filesethook is not None else None
        self.filehook = filehook if filehook is not None else None

        self.g.bind('rico', RICO, override=False)

    def get_graph(self):
        return self.g

    def convert(self) -> None:
        if self.extensions is not None:
            filePattern = [re.compile(extension + "$") for extension in self.extensions]

        for event_directory in os.listdir(self.directory):
            event_filename_with_path = os.path.join(self.directory, event_directory)
            if os.path.isdir(event_filename_with_path):
                event = URIRef(self.corpus_uri_prefix + "/Event/" + quote_plus(event_directory))
                self.g.add((event, RDF.type, RICO.Event))
                self.g.add((event, FieldDataNS.ID, Literal(event_directory)))
                #self.g.add((self.root_node, RICO.Event), event)
                if self.directoryhook is not None:
                    self.directoryhook.directory_hook(self.g, event, event_directory)
                files = os.listdir(event_filename_with_path)
                if self.extensions is not None:
                    files = [
                            f for f in files if any(
                                [p.search(f) for p in filePattern]
                            )
                    ]
                if len(files) > 0:
                    files_by_records = []
                    if self.filesethook is not None:
                        files_by_records = self.filesethook.fileset_hook(files)
                    else:
                        files_by_records = files
                    for i in files_by_records:
                        if isinstance(i, list):
                            if len(i) == 0:
                                raise Exception("empty file set in event: {event}")
                        elif isinstance(i, str):
                            i = [i]
                        else:
                            raise Exception("files_by_records contains either list of string (event: {event})")
                        record_name = i[0]
                        record = URIRef(self.corpus_uri_prefix + "/Event/" + quote_plus(event_directory) + "/Record/" + quote_plus(record_name))
                        self.g.add((record, RDF.type, RICO.Record))
                        self.g.add((record, FieldDataNS.ID, Literal(record_name)))
                        self.g.add((event, RICO.documents, record))
                        for f in i:
                            self._create_instance(record, event_filename_with_path, f)

                        if isinstance(i, list):
                            if self.filehook is not None:
                                for f in i:
                                    self.filehook.file_hook(self.g, record, f)


    def _create_instance(self, record:URIRef, path:str, file:str) -> None:
        instance = URIRef(str(record) + "/" + quote_plus(file))
        self.g.add((record, RICO.hasInstance, instance))
        self.g.add((instance, RDF.type, RICO.Instance))
        self.g.add((instance, FieldDataNS.URL, Literal(os.path.join(path, file))))
        self.g.add((instance, FieldDataNS.FileName, Literal(file)))


