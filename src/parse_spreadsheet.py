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
from rdf4lfd.parser import Parser

class Spreadsheet2RDF(Parser):

    CSV_FORMAT = "CSV"
    ODT_FORMAT = "ODS"

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
    
    spearkersSplittedColName = "spearkersSplitted"
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
    
    def __init__(self, file, format="ODT", sheet_index=1, conf_file=None, context_graph_file=None, corpus_uri_prefix="http://mycorpus", graph_identifier=None):
        with open(conf_file, 'r') as conf_fh:
            self.conf = json.load(conf_fh)

        self.file=file
        self.format=format
        self.sheet_index=sheet_index
        # self.mediaExts = mediaExts
        self.datetimeformat="%Y-%m-%d"

        self.context_graph = Graph()
        if context_graph_file is not None:
            self.context_graph.parse(context_graph_file)
        self._read_input_graph()

        self.generalGraph = ConjunctiveGraph()
        if graph_identifier is None:
            graph_identifier = file
        self.g = Graph(self.generalGraph.store, identifier=Literal(graph_identifier))

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
            read_csv(self.file, header=header)
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
        df[Spreadsheet2RDF.spearkersSplittedColName] = Spreadsheet2RDF.__splitColumn(df[Spreadsheet2RDF.speakerColName])
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
        timeSpanRe = re.compile('^([^{]+)(\{([^:]+):(.+)\})?$')
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

        # Create the fieldtrip events
        fieldtrip = df[Spreadsheet2RDF.fieldSessionIDColName].unique()
        fieldSessionMap = dict()
        for i, f in enumerate(fieldtrip):
            node = self.__createFieldSessionRdfNode(f)
            fieldSessionMap[f] = node
    
        # Create the Session events
        for i, row in df.iterrows():
            eventNodeURIRef = self.__createRDFEvent(
                row,
                df[Spreadsheet2RDF.spearkersSplittedColName][i],
                df[Spreadsheet2RDF.consultantSplittedColName][i],
                df[Spreadsheet2RDF.genreSplittedColName][i],
                df[Spreadsheet2RDF.photoSplittedColName][i],
                df[Spreadsheet2RDF.languageSplittedColName][i]
            )
    
            # Link between the event and the field session event
            self.g.add((fieldSessionMap[df[Spreadsheet2RDF.fieldSessionIDColName]
                  [i]], FieldDataNS.SubEvent, eventNodeURIRef))
    
            # Create the recording set if any
            mediaSourceSetURIRef = None
            if row[Spreadsheet2RDF.mediaObjectColName] is not None:
                mediaSourceSetURIRef = self.__createRDFMediaSourceSet(row[Spreadsheet2RDF.mediaObjectColName])
    
            # Create the reference to notebook if any
            notebookURIRef = None
            # volColName is the col used to test for MEDIA_AND_SESSION... use rather that one?
            if row[Spreadsheet2RDF.sessionIDColName] is not None:
                notebookURIRef = self.__createRDFNotebookRef(row)
    
            rowType = row[Spreadsheet2RDF.rowTypeColName]
    
            if rowType == Spreadsheet2RDF.COL_TYPE_MEDIA_ONLY_ROW:
                if row[Spreadsheet2RDF.mediaObjectColName] is None:
                    raise Exception("Media only row without media file: (row {i})")
                self.g.add((eventNodeURIRef, FieldDataNS.Recording, mediaSourceSetURIRef))
    
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
                self.g.add((eventNodeURIRef, FieldDataNS.EventType,
                      Literal("DataSession", datatype=XSD.string)))
                self.g.add((eventNodeURIRef, FieldDataNS.Product, notebookURIRef))
    
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
                self.g.add((eventNodeURIRef, FieldDataNS.EventType,
                      Literal("DataSession", datatype=XSD.string)))

                self.g.add((eventNodeURIRef, FieldDataNS.Recording, mediaSourceSetURIRef))
                self.g.add((eventNodeURIRef, FieldDataNS.Transcription, notebookURIRef))
    
            notes = None
            if row[Spreadsheet2RDF.notesColName] is not None:
                notes, freecomment = Spreadsheet2RDF.__parseNote(row[Spreadsheet2RDF.notesColName])
                if freecomment is not None:
                    for fc in freecomment:
                        # TODO may point to something else that the event...
                        self.g.add((eventNodeURIRef, FieldDataNS.Comment,
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
                                        (eventNodeURIRef, FieldDataNS.Comment, linkedEventURIRef))
    
                                # It's only an Event "DataSession" that has a recording
                                # already stated in the "genre" field of this event
                                # Should indicate that this event is analyzing the target event
                                elif n[0] == "DataSessionRecording":
                                    self.g.add(
                                        (eventNodeURIRef, FieldDataNS.Analyze, linkedEventURIRef))
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
                                    (eventNodeURIRef, FieldDataNS.Comment, linkedEventURIRef))
                            elif n[0] == "transcription":
                                self.g.add(
                                    (eventNodeURIRef, FieldDataNS.Analyze, linkedEventURIRef))
                            elif n[0] == "continuation":
                                self.g.add(
                                    (eventNodeURIRef, FieldDataNS.Continuation, linkedEventURIRef))
                            # Warning: here link from the context name.
                            # does not occurs in the data
                            # FIXME no need to linkedSourceURIRef to be created here
                            elif n[0] == "stimulus":
                                self.g.add((eventNodeURIRef, FieldDataNS.Stimulus,
                                      Literal(n[1], datatype=XSD.string)))
                            else:
                                raise Exception("Unknown case:" + n[0])
                    elif rowType == Spreadsheet2RDF.COL_TYPE_SESSION_AND_MEDIA_ROW:
                        for n in notes:
                            if n[0] == "MentionInCahier":
                                self.g.add((eventNodeURIRef, FieldDataNS.MentionInNotebook, Literal(
                                    n[1], datatype=XSD.string)))
                            elif n[0] == "stimulus":
                                self.g.add((eventNodeURIRef, FieldDataNS.Stimulus,
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
        notes = [x.strip() for x in field.split(',')]
        edges = list()
        freecomment = list()
        p = re.compile('-\[([A-Za-z]+)\]->([?A-Za-z0-9\.]+)')
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
        l = s.str.split(',\W*')
        return l
        # languagesByRow = [re.split(',\\w*', s) for s in df[CSV2RDF.languageColName].tolist() if s != None]   


    def _read_input_graph(self):
        eventUriByName = dict()
        recordUriByName = dict()
        for s, p, o in self.context_graph.triples((None, RDF.type, RICO.Event)):
            for s2, p2, o2 in self.context_graph.triples((s, FieldDataNS.ID, None)):
                eventUriByName[o2] = s
            
        for s, p, o in self.context_graph.triples((None, RDF.type, RICO.Record)):
            for s2, p2, o2 in self.context_graph.triples((s, FieldDataNS.ID, None)):
                recordUriByName[o2] = s
        self.recordUriByName = recordUriByName
        self.eventUriByName = eventUriByName

    def __populateMediaWithActualDirectoryInCSV(self):
        rows = self.df[Spreadsheet2RDF.mediaObjectColName]
        for row in rows:
            if row == None:
                continue
            for media in row:
                if isinstance(media, FileNameReference):
                    parts = (media.name).split(".")
                    if (len(parts)) < 2:
                        raise Exception(f"{media.name} has no extension, object {media}.")
                    alternateSayMoreName = parts[0] + "_Source." + parts[1]
                    if media.name in self.recordUriByName:
                        media.setDir(self.recordUriByName[media.name])
                    elif alternateSayMoreName in self.recordUriByName:
                        media.setDir(self.recordUriByName[alternateSayMoreName])
                    else:
                        raise Exception(f"No localisation found of file {media.name}, object {media}.")
                elif isinstance(media, SessionReference):
                    media.setDir(self.eventUriByName[media.name])


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


    def __createFieldSessionRdfNode(self, fieldsessionname):
        # warning : fieldsessionname is an int (converted while reading the data frame)
        mName = str(uuid.uuid4())
        fieldSessionNodeURIRef = URIRef(
            FieldDataNS._NS + FieldDataNS.URI_PREFIX_FieldSession + mName)
        self.g.add((fieldSessionNodeURIRef, RDF.type, FieldDataNS.Event))
        self.g.add((fieldSessionNodeURIRef, FieldDataNS.EventType,
              Literal(FieldDataNS.FieldSessionEventType, datatype=XSD.string)))
        self.g.add((fieldSessionNodeURIRef, FieldDataNS.FieldSessionName,
              Literal(str(fieldsessionname), datatype=XSD.string)))
        return fieldSessionNodeURIRef


    def __createRDFEvent(self, row, speakers, consultants, genres, photos, languages):
        mName = str(uuid.uuid4())
        eventNodeURIRef = URIRef(FieldDataNS._NS + FieldDataNS.URI_PREFIX_Event + mName)
        self.g.add((eventNodeURIRef, RDF.type, FieldDataNS.Event))
        self.g.add((eventNodeURIRef, FieldDataNS.Date, Literal(
            row[Spreadsheet2RDF.parsedDateColName], datatype=XSD.date)))

        self.__addMultipleObject(eventNodeURIRef, FieldDataNS.EventType,  genres)
        self.__addMultipleObject(eventNodeURIRef, FieldDataNS.Language,   languages)
        self.__addMultipleObject(eventNodeURIRef, FieldDataNS.Speaker,    speakers)
        self.__addMultipleObject(eventNodeURIRef, FieldDataNS.Consultant, consultants)
        self.__addMultipleObject(eventNodeURIRef, FieldDataNS.Photo,      photos)

        self.g.add((eventNodeURIRef, FieldDataNS.Title, Literal(
            row[Spreadsheet2RDF.descriptionColName], datatype=XSD.string)))
        return eventNodeURIRef

    def __addMultipleObject(self, subject, predicate, objects):
        if objects is not None:
            for o in objects:
                self.g.add((subject, predicate,
                      Literal(o, datatype=XSD.string)))


    def __createRDFMediaSourceSet(self, medias):
        """
        a MediaSourceSet point to one or more MediaRef :
    
        a FieldDataNS.MediaSourceSet----[FieldDataNS.MediaSource]----->a FieldDataNS.MediaRef
    
        a media ref holds the physical information:
    
        a FieldDataNS.MediaRef----[FieldDataNS.FileName]--->Literal(file URI)
                             ----[FieldDataNS.DirName]--->Literal(dir URI)
                             ----[FieldDataNS.StartSpan]--->Literal(dir URI)
                             ----[FieldDataNS.EndSpan]--->Literal(dir URI)
    
        """
        mName = str(uuid.uuid4())
        mediaSourceSet = URIRef(FieldDataNS._NS +
                                FieldDataNS.URI_PREFIX_MediaSourceSet + mName)
        self.g.add((mediaSourceSet, RDF.type, FieldDataNS.MediaSourceSet))
        for m in medias:
            media = URIRef(
                FieldDataNS._NS + FieldDataNS.URI_PREFIX_MediaReference + mName + ":" + m.name)
            self.g.add((media, RDF.type, FieldDataNS.MediaRef))
            self.g.add((mediaSourceSet, FieldDataNS.MediaSource, media))
            self.g.add((media, FieldDataNS.FileName,
                  Literal(m.name, datatype=XSD.anyURI)))
            if isinstance(m, LocalizedMediaReference):
                self.g.add((media, FieldDataNS.DirName, Literal(m.dir, datatype=XSD.anyURI)))
            #g.add((mediaRefNodeName, FieldDataNS.MediaScene, Literal(localized_media[0][0])))
            # FIXME Could in theory appears for each file, but in practice only on length-1 set
            if isinstance(m, FileNameReference) and m.hasTimestamp():
                self.g.add((media, FieldDataNS.StartSpan,
                      Literal(m.start_timestamp, datatype=XSD.string)))
                self.g.add((media, FieldDataNS.EndSpan,
                      Literal(m.end_timestamp, datatype=XSD.string)))
        return mediaSourceSet
    
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
        self.hasTimestamp = False

    def setTimestamp(self, start, end):
        self.start_timestamp = start
        self.end_timestamp = end
        self.hasTimestamp =  True

    def hasTimestamp(self):
        return self.hasTimestamp

class SessionReference(LocalizedMediaReference):
    pass

