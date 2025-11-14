import collections
from urllib.parse import non_hierarchical
from pandas_ods_reader import read_ods
from pandas import read_csv
import pandas as pd
from pathlib import Path
import re
from rdflib import Graph, ConjunctiveGraph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import FOAF, XSD
import glob
import os
import numpy as np
import uuid
import json
from rdf4lfd.fielddata_namespace import FieldDataNS
from rdf4lfd.rico_namespace import RICO
from lameta_namespace import LametaNS
from rdf4lfd.converter import Converter
from urllib.parse import quote_plus

class Spreadsheet2RDF(Converter):

    CSV_FORMAT = "CSV"
    ODT_FORMAT = "ODS"

    # For creating the URI
    URI_PREFIX_MediaSourceSet = 'MediaSourceSet-'
    URI_PREFIX_Event = "Event-"
    URI_PREFIX_FieldSession = "FieldSession-"
    URI_PREFIX_WrittenSource = 'WrittenSource-'
    URI_PREFIX_MediaReference = "MediaReference-"
    Missing = "Missing"
    FieldSessionEventType = "FieldSession"

    fieldSessionIDColName = "FieldSessionID"
    dateColName = 'Date'
    mediaFileNameColName = 'MediaFileName'
    sessionIDColName = 'SessionID'
    speakerColName = 'Speaker'
    consultantColName = 'Consultant'
    genreColName = 'Genre'
    languageColName = 'Language'
    descriptionColName = 'Description'
    durationColName = 'Duration'
    transcritDansCahierColName = 'Transcrit dans cahier'
    volColName = 'vol.'
    pageNumberColName = 'PageNumber'
    elanColName = 'Elan'
    associatedPhotoColName = 'AssociatedPhoto'
    notesColName = 'Notes'
    elanFileColName = 'ElanFile'
    
    rowTypeColName = 'RowType'
    qualifiedSessionNameColName = 'QualifiedName'
    
    speakersSplittedColName = "spearkersSplitted"
    consultantSplittedColName = "consultantSplitted"
    genreSplittedColName = "genreSplitted"
    photoSplittedColName = "photoSplitted"
    languageSplittedColName = "languageSplitted"
    parsedDateColName = "parsedDate"
    mediaObjectColName = "mediaSplitted"
    
    COL_TYPE_SESSION_ONLY_ROW = 1
    COL_TYPE_MEDIA_ONLY_ROW = 2
    COL_TYPE_SESSION_AND_MEDIA_ROW = 3
    COL_TYPE_NEW_DATE_ROW = 4
    
    SESSION_PREFIX = "s:"
    LOST_PREFIX = "perdu:"
    
    def __init__(self, file,
                 format="ODT",
                 sheet_index=1,
                 conf_file=None,
                 context_graph_file=None,
                 corpus_uri_prefix="http://mycorpus/",
                 graph_identifier=None
                ):
        
        with open(conf_file, 'r') as conf_fh:
            self.conf = json.load(conf_fh)

        self.corpus_uri_prefix = corpus_uri_prefix
        self.file=file
        self.format=format
        self.sheet_index=sheet_index
        # self.mediaExts = mediaExts
        self.datetimeformat="%Y-%m-%d"

        self.context_graph = Graph()
        if context_graph_file is not None:
            self.context_graph.parse(context_graph_file)
        self._populate_map_out_of_context_graph()

        self.generalGraph = ConjunctiveGraph()
        if graph_identifier is None:
            graph_identifier = file
        self.g = Graph(self.generalGraph.store, identifier=Literal(graph_identifier))
        self.g.namespace_manager.bind('rico', RICO, override=False)
        self.g.namespace_manager.bind('mydata', corpus_uri_prefix, override=False)

        self.speakerRoleTypeURIRef = URIRef(self.corpus_uri_prefix + FieldDataNS.URI_PREFIX_RoleType + "Speaker")
        self.g.add((self.speakerRoleTypeURIRef, RDF.type,      RICO.ROLE_TYPE))
        self.g.add((self.speakerRoleTypeURIRef, RICO.name,     Literal("Speaker", datatype=XSD.string)))

        self.consultantRoleTypeURIRef = URIRef(self.corpus_uri_prefix + FieldDataNS.URI_PREFIX_RoleType + "Consultant")
        self.g.add((self.consultantRoleTypeURIRef, RDF.type,      RICO.ROLE_TYPE))
        self.g.add((self.consultantRoleTypeURIRef, RICO.name,     Literal("Consultant", datatype=XSD.string)))

        print(f"* Read csv file {self.file} (sheet {str(self.sheet_index)})")
        self.__read_spreadsheet()

    def convert(self):
        print("* Add filesystem paths to media file names and directory names found in csv")
        self.__populateMediaWithActualDirectoryInCSV()

        print("* Create RDF graph")
        self.__createRdfGraph()

    def get_graph(self) -> Graph:
        return self.generalGraph

    def __read_spreadsheet(self):
        header=self.conf["header"]
        if header is None:
            header = 'infer'
        elif header == "True":
            header = 1
        elif header == "False":
            header = 0
        else:
            raise Exception("Unknown header value in configuration file: {header}. Possible values are True or False.")

        df = None
        if self.format == Spreadsheet2RDF.CSV_FORMAT:
            df = read_csv(self.file, header=header)
        elif self.format == Spreadsheet2RDF.ODT_FORMAT:
            df = read_ods(self.file, self.sheet_index, headers=header)
        else:
            raise Exception(f"Unknown format: {self.format}")

        # add the row type info to the table (4 different row types)
        rowTypeNewColumn = df.apply(Spreadsheet2RDF.__getRowType, axis=1)
        rowType: list = rowTypeNewColumn.tolist()
        df[Spreadsheet2RDF.rowTypeColName] = rowType
    
        # remove the rows in the data that are only indicating a new day
        df = df.loc[np.array(rowType) != Spreadsheet2RDF.COL_TYPE_NEW_DATE_ROW]
    
        # Create qualified session name
        df[Spreadsheet2RDF.sessionIDColName] = df[Spreadsheet2RDF.sessionIDColName].astype(str)
        df[Spreadsheet2RDF.fieldSessionIDColName] = df[Spreadsheet2RDF.fieldSessionIDColName].astype(int)
        qualifiedNameNewColumn = df.apply(Spreadsheet2RDF.__getQualifiedSessionName, axis=1)
        df[Spreadsheet2RDF.qualifiedSessionNameColName] = qualifiedNameNewColumn
    
        # For every nested list, should check for "" in nested.
        df[Spreadsheet2RDF.speakersSplittedColName] = Spreadsheet2RDF.__splitColumn(df[Spreadsheet2RDF.speakerColName])
        df[Spreadsheet2RDF.consultantSplittedColName] = Spreadsheet2RDF.__splitColumn(df[Spreadsheet2RDF.consultantColName])
        df[Spreadsheet2RDF.genreSplittedColName] = Spreadsheet2RDF.__splitColumn(df[Spreadsheet2RDF.genreColName])
        df[Spreadsheet2RDF.associatedPhotoColName] = df[Spreadsheet2RDF.associatedPhotoColName].apply(
            lambda x: str(x) if isinstance(x, float) else x)
        df[Spreadsheet2RDF.photoSplittedColName] = Spreadsheet2RDF.__splitColumn(df[Spreadsheet2RDF.associatedPhotoColName])
        df[Spreadsheet2RDF.languageSplittedColName] = Spreadsheet2RDF.__splitColumn(df[Spreadsheet2RDF.languageColName])
    
        df[Spreadsheet2RDF.parsedDateColName] = df[Spreadsheet2RDF.dateColName].apply(
            pd.to_datetime, format=self.datetimeformat)

        mediaRowSplitted = Spreadsheet2RDF.__splitColumn(df[Spreadsheet2RDF.mediaFileNameColName])
        df[Spreadsheet2RDF.mediaObjectColName] = Spreadsheet2RDF.__createRowMedia(mediaRowSplitted)

        self.df = df

    def __createRowMedia(mediaRowSplitted):
        timeSpanRe = re.compile(r'^([^{]+)(\{([^:]+):(.+)\})?$')
        lostRe     = re.compile(Spreadsheet2RDF.LOST_PREFIX)
        sessionRe  = re.compile(Spreadsheet2RDF.SESSION_PREFIX)
        res = [None] * len(mediaRowSplitted)
        for i, ms in enumerate(mediaRowSplitted):
            if ms == None:
                continue
            row = []
            for m in ms:
                if m.startswith(Spreadsheet2RDF.LOST_PREFIX): #lostRe.match(m):
                    row.append(LostReference(m.partition(Spreadsheet2RDF.LOST_PREFIX)[2]))
                elif m.startswith(Spreadsheet2RDF.SESSION_PREFIX): #sessionRe.match(m):
                    row.append(SessionReference(m.partition(Spreadsheet2RDF.SESSION_PREFIX)[2]))
                else:
                    assert m != "", "media filename cannot be empty string %s" % (i,)
                    group = timeSpanRe.match(m).group(1, 2, 3, 4)
                    f = FileNameReference(group[0])
                    if group[2:4] != None:
                        f.setTimestamp(group[2], group[3])
                    row.append(f)
            res[i] = row
        return res


    def __createRdfGraph(self):
        df = self.df

        # Create the Persons
        self.person_id2URIRef_Map = dict()
        speakers = df[Spreadsheet2RDF.speakersSplittedColName].explode().dropna().unique()
        for i, p in enumerate(speakers):
            node = self.__createPersons(p)
            self.person_id2URIRef_Map[p] = node
        consultants = df[Spreadsheet2RDF.consultantSplittedColName].explode().dropna().unique()
        for i, c in enumerate(consultants):
            node = self.__createPersons(c)
            self.person_id2URIRef_Map[c] = node

        # Create the languages
        self.languages_id2URIRef_Map = dict()
        languages = df[Spreadsheet2RDF.languageSplittedColName].explode().dropna().unique()
        for i, l in enumerate(languages):
            node = self.__createLanguages(l)
            self.languages_id2URIRef_Map[l] = node

        # Create the fieldtrip events
        self.fieldTrip_id2URIRef_Map = dict()
        fieldtrip = df[Spreadsheet2RDF.fieldSessionIDColName].unique()
        for i, f in enumerate(fieldtrip):
            node = self.__createFieldTripResource(f)
            self.fieldTrip_id2URIRef_Map[f] = node
    
        # Create the Session events
        for i, row in df.iterrows():
            event_URIRef = self.__createEventResource(
                row,
                df[Spreadsheet2RDF.genreSplittedColName][i],
                df[Spreadsheet2RDF.photoSplittedColName][i]
            )

            # Link to languages    
            lgs = df[Spreadsheet2RDF.languageSplittedColName][i]
            if lgs is not None:
                for l in lgs:
                    self.g.add((event_URIRef, RICO.hasOrHadLanguage, self.languages_id2URIRef_Map[l]))
                    # This is not correct since language is a property of the record in RICO

            # Speakers
            speakers = df[Spreadsheet2RDF.speakersSplittedColName][i]
            if speakers is not None:
                for s in speakers:
                    creationRelationURIRef = URIRef(self.corpus_uri_prefix + FieldDataNS.URI_PREFIX_CREATIONRELATION + str(uuid.uuid4()))
                    self.g.add((creationRelationURIRef, RDF.type,      RICO.CREATION_RELATION))
                    self.g.add((creationRelationURIRef, RICO.hasTarget, self.person_id2URIRef_Map[s]))
                    self.g.add((creationRelationURIRef, RICO.hasSource, event_URIRef))
                    self.g.add((creationRelationURIRef, RICO.roleIsContextOfCreationRelation, self.speakerRoleTypeURIRef))

            # Consultants
            consultants = df[Spreadsheet2RDF.consultantSplittedColName][i]
            if consultants is not None:
                for c in consultants:
                    creationRelationURIRef = URIRef(self.corpus_uri_prefix + FieldDataNS.URI_PREFIX_CREATIONRELATION + str(uuid.uuid4()))
                    self.g.add((creationRelationURIRef, RDF.type,      RICO.CREATION_RELATION))
                    self.g.add((creationRelationURIRef, RICO.hasTarget, self.person_id2URIRef_Map[c]))
                    self.g.add((creationRelationURIRef, RICO.hasSource, event_URIRef))
                    self.g.add((creationRelationURIRef, RICO.roleIsContextOfCreationRelation, self.consultantRoleTypeURIRef))

            # Link between the event and the field session event
            session_trip_id = df[Spreadsheet2RDF.fieldSessionIDColName][i]
            self.g.add((self.fieldTrip_id2URIRef_Map[session_trip_id], RICO.SubEvent, event_URIRef))
    
            # Create the recording set if any
            mediaSourceSetURIRef = None
            if row[Spreadsheet2RDF.mediaObjectColName] is not None:
                mediaSourceSetURIRef = self.__createRecordSetResource(row[Spreadsheet2RDF.mediaObjectColName])
    
            # TODO reprendre ici
            # Create the reference to notebook if any
            notebookURIRef = None
            # volColName is the col used to test for MEDIA_AND_SESSION... use rather that one?
            if row[Spreadsheet2RDF.sessionIDColName] is not None:
                notebookURIRef = self.__createRDFNotebookRef(row)
    
            rowType = row[Spreadsheet2RDF.rowTypeColName]
            if rowType == Spreadsheet2RDF.COL_TYPE_MEDIA_ONLY_ROW:
                if row[Spreadsheet2RDF.mediaObjectColName] is None:
                    raise Exception("Media only row without media file: (row {i})")
                self.g.add((event_URIRef, RICO.isDocumentedBy, mediaSourceSetURIRef)) # TODO voc check
    
            # Case 2: Session without media
            #         -> Go into EADFieldnote
            #         -> In Graph, WrittenDocument node. Link to EADFieldNote
            #         -> if Notes edges, do edges in Graph:
            #            if node -[transcription]-> link to target (Text type) with edge type = transcription
            #            if node -[comment]-> link to target (Text type) with edge type = comment
            #            if node -[stimulus]-> link from target (Text type) to StimulusID with edge type = stimulus
            #         -> if -[continuation]-> link the WrittenDocument to the WrittenDocument and the Text
            elif rowType == Spreadsheet2RDF.COL_TYPE_SESSION_ONLY_ROW:
                # FIXME what about the existing genre? should be erased
                self.g.add((event_URIRef, FieldDataNS.EventType,
                      Literal("DataSession", datatype=XSD.string)))
                self.g.add((event_URIRef, FieldDataNS.Product, notebookURIRef))
    
            # Case 3: session and media
            #         -> Make both case 2 and 3.
            #              note : Il ne peut pas y avoir deux fois "comment".
            #              note : il pourrait y avoir deux fois "stimulus"
            #         -> In Graph, link both node to Text node:
            #            NON if SessionID match "t" : WrittenDocument-[transcription]->text
            #            NON else: WrittenDocument-[notation]->text
            #            WrittenDocument-[transcription]->text
            #         -> if -[continuation]-> ERROR
            elif rowType == Spreadsheet2RDF.COL_TYPE_SESSION_AND_MEDIA_ROW:
    
                # There is BOTH a performance event and a datasession event
                # sometime the two are contiguous, sometime there is two different dates...
                # FIXME find the session associated with a recording belonging to another event
    
                # This gender is added to the existing gender of the first Event
                self.g.add((event_URIRef, FieldDataNS.EventType,
                      Literal("DataSession", datatype=XSD.string)))

                self.g.add((event_URIRef, FieldDataNS.Recording, mediaSourceSetURIRef))
                self.g.add((event_URIRef, FieldDataNS.Transcription, notebookURIRef))
    
            notes = None
            if row[Spreadsheet2RDF.notesColName] is not None:
                notes, freecomment = Spreadsheet2RDF.__parseNote(row[Spreadsheet2RDF.notesColName])
                if freecomment is not None:
                    for fc in freecomment:
                        # TODO may point to something else that the event...
                        self.g.add((event_URIRef, FieldDataNS.Comment,
                              Literal(fc, datatype=XSD.string)))
                if notes is not None:  # FIXME and if there is no note ???
                    if rowType == Spreadsheet2RDF.COL_TYPE_MEDIA_ONLY_ROW:
                        for n in notes:
                            if n[0] == "MentionInCahier":
                                # TODO may point to something else that the mediaSet?
                                # TODO how to link this to notebook?
                                self.g.add(
                                    (mediaSourceSetURIRef, FieldDataNS.Mention, Literal(n[1])))
                            else:
                                # TODO
                                # if note = comment or DataSessionRecording
                                # -> In Graph, Make a MediaDocument. Use the timestamp if present in the media file column
    
                                # Create the event pointed at in the structured note
    
                                # FIXME will correctly retrieve the thing?
                                # FIXME Should point to the Event, not the WrittenSource?
                                linkedSourceURIRef = URIRef(
                                    FieldDataNS._NS + FieldDataNS.URI_PREFIX_WrittenSource + n[1])
                                linkedEventURIRef = self.g.value(
                                    predicate=FieldDataNS.Transcription, object=linkedSourceURIRef)
                                if linkedEventURIRef is None:
                                    linkedEventURIRef = Literal("Not found!")
    
                                # Link to the event pointed at
    
                                if n[0] == "comment":
                                    self.g.add(
                                        (event_URIRef, FieldDataNS.Comment, linkedEventURIRef))
    
                                # It's only an Event "DataSession" that has a recording
                                # already stated in the "genre" field of this event
                                # Should indicate that this event is analyzing the target event
                                elif n[0] == "DataSessionRecording":
                                    self.g.add(
                                        (event_URIRef, FieldDataNS.Analyze, linkedEventURIRef))
                                else:
                                    raise Exception("Unknown case:" + n[0])
                    elif rowType == Spreadsheet2RDF.COL_TYPE_SESSION_ONLY_ROW:
                        for n in notes:
                            # FIXME duplicate code with just above
                            linkedSourceURIRef = URIRef(
                                FieldDataNS._NS + FieldDataNS.URI_PREFIX_WrittenSource + n[1])
                            # print(linkedSourceURIRef)
                            linkedEventURIRef = self.g.value(
                                predicate=FieldDataNS.Transcription, object=linkedSourceURIRef)
                            if linkedEventURIRef is None:
                                linkedEventURIRef = Literal("Not found!")
    
                            if n[0] == "comment":
                                self.g.add(
                                    (event_URIRef, FieldDataNS.Comment, linkedEventURIRef))
                            elif n[0] == "transcription":
                                self.g.add(
                                    (event_URIRef, FieldDataNS.Analyze, linkedEventURIRef))
                            elif n[0] == "continuation":
                                self.g.add(
                                    (event_URIRef, FieldDataNS.Continuation, linkedEventURIRef))
                            # Warning: here link from the context name.
                            # does not occurs in the data
                            # FIXME no need to linkedSourceURIRef to be created here
                            elif n[0] == "stimulus":
                                self.g.add((event_URIRef, FieldDataNS.Stimulus,
                                      Literal(n[1], datatype=XSD.string)))
                            else:
                                raise Exception("Unknown case:" + n[0])
                    elif rowType == Spreadsheet2RDF.COL_TYPE_SESSION_AND_MEDIA_ROW:
                        for n in notes:
                            if n[0] == "MentionInCahier":
                                self.g.add((event_URIRef, FieldDataNS.MentionInNotebook, Literal(
                                    n[1], datatype=XSD.string)))
                            elif n[0] == "stimulus":
                                self.g.add((event_URIRef, FieldDataNS.Stimulus,
                                      Literal(n[1], datatype=XSD.string)))
                            else:
                                raise Exception("Unknown case:" + n[0])
    
            # In all cases, if there is photo:
            #         -> Go into EADPhoto
            #            add to ref photo in Text node
            #            add to ref photo in Text node
            #            if -[writtenSource]-> : created WrittenDocument and link to photo.


    def __parseNote(field):
        """
        split the string on comma and look for edges expressed
        as -[type]->target.
        return a tuple containing:
          - a list of tuple (type, target)
          - a list of other free comment found
        """
        notes = [x.strip() for x in field.split(r',')]
        edges = list()
        freecomment = list()
        p = re.compile(r'-\[([A-Za-z]+)\]->([?A-Za-z0-9\.]+)')
        for n in notes:
            m = p.match(n)
            if m is not None:
                edges.append(m.group(1, 2))
            else:
                freecomment.append(n)
        if len(edges) == 0:
            edges = None
        return (edges, freecomment)


    def __splitColumn(col):
        s = pd.Series(col)  # , dtype=str
        l = s.str.split(r',\W*')
        return l
        # languagesByRow = [re.split(',\\w*', s) for s in df[CSV2RDF.languageColName].tolist() if s != None]   


    def _populate_map_out_of_context_graph(self):
        uriMatcher = re.compile(r'^.+/([^/]+)$')

        eventUriById = dict()
        for s, p, o in self.context_graph.triples((None, RDF.type, LametaNS.Session)):
            for s2, p2, o2 in self.context_graph.triples((s, LametaNS.id, None)):
                eventUriById[str(o2)] = str(s)
        self.eventUriById = eventUriById
          
        recordUriById = dict()
        for s, p, o in self.context_graph.triples((None, RDF.type, LametaNS.FILE)):
            for s2, p2, o2 in self.context_graph.triples((s, LametaNS.FILE_URL, None)):
                m = uriMatcher.match(str(o2))
                if m is None:
                    print(f"WARNING: cannot extract file id out of {o2}")
                    continue
                else:
                    recordUriById[m.group(1)] = str(o2)
        self.recordUriById = recordUriById

    def __populateMediaWithActualDirectoryInCSV(self):
        rows = self.df[Spreadsheet2RDF.mediaObjectColName]
        #print(self.recordUriById)
        for row in rows:
            if row == None:
                continue
            for media in row:
                if isinstance(media, FileNameReference):
                    parts = (media.name).split(r".")
                    if (len(parts)) < 2:
                        raise Exception(f"{media.name} has no extension, object {media}.")
                    alternateSayMoreName = parts[0] + "_Source." + parts[1]
                    if media.name in self.recordUriById:
                        media.setDir(self.recordUriById[media.name])
                    elif alternateSayMoreName in self.recordUriById:
                        media.setDir(self.recordUriById[alternateSayMoreName])
                    else:
                        raise Exception(f"No localisation found of file {media.name}, object {media}.")
                elif isinstance(media, SessionReference):
                    media.setDir(self.eventUriById[media.name])


    def __getQualifiedSessionName(row):
        # TODO new rules in 2019
        if row[Spreadsheet2RDF.rowTypeColName] == Spreadsheet2RDF.COL_TYPE_MEDIA_ONLY_ROW:
            return None
        elif re.match('S', row[Spreadsheet2RDF.sessionIDColName]):
            return str(row[Spreadsheet2RDF.fieldSessionIDColName]) + '.' + str(row[Spreadsheet2RDF.volColName]) + '.' + row[Spreadsheet2RDF.sessionIDColName]
        else:
            return str(row[Spreadsheet2RDF.fieldSessionIDColName]) + row[Spreadsheet2RDF.sessionIDColName]


    def __getRowType(row):
        """Analyze the row and select between one of three types:
            - the row describe a multimedia record only
            - the row describe a fieldnote book record only
            - the row declare a fieldnote book session linked to a multimedia record"""
        if row[Spreadsheet2RDF.sessionIDColName] == None and row[Spreadsheet2RDF.mediaFileNameColName] != None:
            return Spreadsheet2RDF.COL_TYPE_MEDIA_ONLY_ROW
        elif row[Spreadsheet2RDF.sessionIDColName] != None and row[Spreadsheet2RDF.mediaFileNameColName] == None:
            return Spreadsheet2RDF.COL_TYPE_SESSION_ONLY_ROW
        elif row[Spreadsheet2RDF.sessionIDColName] != None and row[Spreadsheet2RDF.mediaFileNameColName] != None:
            return Spreadsheet2RDF.COL_TYPE_SESSION_AND_MEDIA_ROW
        # row[CSV2RDF.fieldSessionIDColName].match(r'Le |Lundi|Mardi|Mercredi|Jeudi|Vendredi|Samedi|Dimanche'):
        elif row[Spreadsheet2RDF.fieldSessionIDColName] != None and type(row[Spreadsheet2RDF.fieldSessionIDColName]) is str:
            return Spreadsheet2RDF.COL_TYPE_NEW_DATE_ROW
        else:
            print(f"Unknown case: {str(row)}")
            return 0

    def __createPersons(self, person_id:str):
        idPerson = str(uuid.uuid4())
        idName = str(uuid.uuid4())

        personNodeURIRef = URIRef(self.corpus_uri_prefix + FieldDataNS.URI_PREFIX_Person + idPerson)
        nameNodeURIRef = URIRef(self.corpus_uri_prefix + FieldDataNS.URI_PREFIX_Name + idName)

        self.g.add((personNodeURIRef, RDF.type,       RICO.Person))
        self.g.add((nameNodeURIRef,   RDF.type,       RICO.Name))

        self.g.add((personNodeURIRef, RICO.hasOrHadName,  nameNodeURIRef))
        self.g.add((nameNodeURIRef,   RICO.fullName,     Literal(str(person_id), datatype=XSD.string)))
        return personNodeURIRef
    
    def __createLanguages(self, languages:str):
        mName = str(uuid.uuid4())
        languageNodeURIRef = URIRef(self.corpus_uri_prefix + FieldDataNS.URI_PREFIX_Language + mName)
        self.g.add((languageNodeURIRef, RDF.type,      RICO.Language))
        self.g.add((languageNodeURIRef, RICO.name, Literal(str(languages), datatype=XSD.string)))
        return languageNodeURIRef
    
    def __createFieldTripResource(self, fieldsessionname:int):
        # warning : fieldsessionname is an int (converted while reading the data frame)
        mName = str(uuid.uuid4())
        fieldSessionNodeURIRef = URIRef(self.corpus_uri_prefix + FieldDataNS.URI_PREFIX_FieldSession + mName)
        self.g.add((fieldSessionNodeURIRef, RDF.type,                     RICO.Event))
        self.g.add((fieldSessionNodeURIRef, RICO.EventType,               Literal(FieldDataNS.FieldSessionEventType, datatype=XSD.string)))
        self.g.add((fieldSessionNodeURIRef, FieldDataNS.FieldSessionName, Literal(str(fieldsessionname), datatype=XSD.string)))
        return fieldSessionNodeURIRef

    def __createEventResource(self, row, genres, photos):
        mName = str(uuid.uuid4())
        eventNodeURIRef = URIRef(self.corpus_uri_prefix + FieldDataNS.URI_PREFIX_Event + mName)
        self.g.add((eventNodeURIRef, RDF.type,  RICO.Event))
        self.g.add((eventNodeURIRef, RICO.Date, Literal(row[Spreadsheet2RDF.parsedDateColName], datatype=XSD.date)))

        self.__addMultipleObject(eventNodeURIRef, RICO.EventType,  genres)
        self.__addMultipleObject(eventNodeURIRef, RICO.Photo,      photos)

        self.g.add((eventNodeURIRef, FieldDataNS.Title, Literal(row[Spreadsheet2RDF.descriptionColName], datatype=XSD.string)))
        return eventNodeURIRef

    def __addMultipleObject(self, subject, predicate, objects):
        if objects is not None:
            for o in objects:
                self.g.add((subject, predicate,
                      Literal(o, datatype=XSD.string)))


    def __createRecordSetResource(self, medias):
        """
        Points to one or more MediaRef :
    
        a FieldDataNS.MediaSourceSet----[FieldDataNS.MediaSource]----->a FieldDataNS.MediaRef
    
        a media ref holds the physical information:
    
        a FieldDataNS.MediaRef----[FieldDataNS.FileName]--->Literal(file URI)
                             ----[FieldDataNS.DirName]--->Literal(dir URI)
                             ----[FieldDataNS.StartSpan]--->Literal(dir URI)
                             ----[FieldDataNS.EndSpan]--->Literal(dir URI)
    
        """
        recordSet_id = str(uuid.uuid4())
        recordSetURI = URIRef(self.corpus_uri_prefix + FieldDataNS.URI_PREFIX_MediaSourceSet + recordSet_id)
        self.g.add((recordSetURI, RDF.type, RICO.RecordSet))
        for m in medias:
            recordURI = URIRef(self.corpus_uri_prefix + FieldDataNS.URI_PREFIX_MediaReference + "Record" + "_" + quote_plus(str(m.name))) # TODO is the quote_plus at the right place?
            self.g.add((recordURI, RDF.type, RICO.Record))
            self.g.add((recordSetURI, RICO.hasPart, recordURI)) # check voc
            self.g.add((recordURI, RICO.name, Literal(m.name, datatype=XSD.anyURI)))

            instanceURI = URIRef(self.corpus_uri_prefix + FieldDataNS.URI_PREFIX_MediaReference + "Instance" + "_" + quote_plus(str(m.name))) # TODO is the quote_plus at the right place?
            self.g.add((instanceURI, RDF.type, RICO.Instanciation))
            self.g.add((recordURI, RICO.hasInstantiation, instanceURI)) # TODO check voc

            if isinstance(m, LocalizedMediaReference):
                self.g.add((instanceURI, RICO.DirName, Literal(m.dir, datatype=XSD.anyURI))) # voc
            #g.add((mediaRefNodeName, FieldDataNS.MediaScene, Literal(localized_media[0][0])))
            # FIXME Could in theory appears for each file, but in practice only on length-1 set
            if isinstance(m, FileNameReference) and m.hasTimestamp():
                self.g.add((instanceURI, RICO.StartSpan, Literal(m.start_timestamp, datatype=XSD.string))) # voc
                self.g.add((instanceURI, RICO.EndSpan, Literal(m.end_timestamp, datatype=XSD.string))) # voc
        return recordSetURI
    
    def __createRDFNotebookRef(self, row):
        qName = row[Spreadsheet2RDF.qualifiedSessionNameColName]
        if qName is None:
            qName = FieldDataNS.Missing
        notebookURIRef = URIRef(FieldDataNS._NS +
                                FieldDataNS.URI_PREFIX_WrittenSource + qName)
        self.g.add((notebookURIRef, RDF.type, FieldDataNS.NotebookRef))
        self.g.add((notebookURIRef, FieldDataNS.qualifiedName,
              Literal(qName, datatype=XSD.anyURI)))
        self.g.add((notebookURIRef, FieldDataNS.NotebookVol,
              Literal(row[Spreadsheet2RDF.volColName], datatype=XSD.anyURI)))
        self.g.add((notebookURIRef, FieldDataNS.NotebookPage, Literal(
            row[Spreadsheet2RDF.pageNumberColName], datatype=XSD.anyURI)))
        self.g.add((notebookURIRef, FieldDataNS.otherFlexComText, Literal("")))
        return notebookURIRef

class MediaReference():
    def __init__(self, name):
        self.name = name


class LostReference(MediaReference):
    pass

class LocalizedMediaReference(MediaReference):

    def setDir(self, dir):
        self.dir = dir

class FileNameReference(LocalizedMediaReference):

    def __init__(self, name):
        super().__init__(name)
        self._hasTimestamp = False

    def setTimestamp(self, start, end):
        self.start_timestamp = start
        self.end_timestamp = end
        self._hasTimestamp =  True

    def hasTimestamp(self):
        return self._hasTimestamp

class SessionReference(LocalizedMediaReference):
    pass
