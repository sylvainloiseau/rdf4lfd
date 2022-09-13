import collections
from pandas_ods_reader import read_ods
import pandas as pd
from pathlib import Path
import re
from rdflib import Graph, ConjunctiveGraph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import FOAF, XSD
import glob
import os
import numpy as np
import uuid

class Ric4Fielddata():
    # Prefix for generating IRI
    URI_PREFIX_MediaSourceSet = 'MediaSourceSet-'
    URI_PREFIX_Event = "Event-"
    URI_PREFIX_FieldSession = "FieldSession-"
    URI_PREFIX_WrittenSource = 'WrittenSource-'
    URI_PREFIX_MediaReference = "MediaReference-"
    Missing = "Missing"

    FieldSessionEventType = "FieldSession"

    Rdf4CorpusVocabulary = "http://www.fieldwork-vocabulary.com/#"
    Rdf4Corpus = Namespace(Rdf4CorpusVocabulary)

class CSV2RDF():

    colName = dict()
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
    
    def __init__(self,
        cvs_file="sample/ods/Index.ods",
        sheet_index=1,
        media_dir="/media/sylvain/TerrainBure/SayMore/Tuwari/Sessions/",
        dest_file="sample/Index.ttl",
        context = "http://tuwari.huma-num.fr/corpus/tuwari/#",
        mediaExts = [".MOV", ".WAV", ".MTS", ".wav", ".wma"],
        datetimeformat="%Y-%m-%d"
        ):
        self.cvs_file=cvs_file
        self.sheet_index=sheet_index
        self.media_dir=media_dir
        self.dest_file=dest_file
        self.mediaExts = mediaExts
        self.datetimeformat=datetimeformat

        contextNS = Namespace(context)
        self.generalGraph = ConjunctiveGraph()
        self.g = Graph(self.generalGraph.store, contextNS.CSV)

        print(f"* Read csv file {self.cvs_file} (sheet {str(self.sheet_index)})")
        self.__read_csv()


    def report(self):
        # print(f"{len(dirlist)} directory read")

        # # list the available suffix for checking
        # flat = [f for directory in fileListList for f in directory]
        # p = re.compile('^.+\.([^.]+)$')
        # f = [p.match(f).group(1) for f in flat]
        # flist = collections.Counter(f)
        # for k, v in flist.items():
        #     print(f"{k}: {str(v)}")
        # print("Actually selected: " + ",".join(self.mediaExts))

        # print(f"{len(fileInfoByName.keys())} media files found in the filesystem")

        pass

    def convert(self):
        print("* Scan media directory for media files")
        self.__localizeMedia()
    
        print("* Add filesystem paths to media file names and directory names found in csv")
        self.__populateMediaWithActualDirectory()

        print("* Create RDF graph")
        self.__createRdfGraph()

        print(f"* Serialize RDF graph {self.dest_file}")
        self.generalGraph.serialize(destination=self.dest_file, format="ttl")


    def __read_csv(self):  
        df = read_ods(self.cvs_file, self.sheet_index, headers=True)
    
        # add the row type info to the table (4 different row types)
        rowTypeNewColumn = df.apply(CSV2RDF.__getRowType, axis=1)
        rowType: list = rowTypeNewColumn.tolist()
        df[CSV2RDF.rowTypeColName] = rowType
    
        # remove the rows in the data that are only indicating a new day
        df = df.loc[np.array(rowType) != CSV2RDF.COL_TYPE_NEW_DATE_ROW]
    
        # Create qualified session name
        df[CSV2RDF.sessionIDColName] = df[CSV2RDF.sessionIDColName].astype(str)
        df[CSV2RDF.fieldSessionIDColName] = df[CSV2RDF.fieldSessionIDColName].astype(int)
        qualifiedNameNewColumn = df.apply(CSV2RDF.__getQualifiedSessionName, axis=1)
        df[CSV2RDF.qualifiedSessionNameColName] = qualifiedNameNewColumn
    
        # For every nested list, should check for "" in nested.
        df[CSV2RDF.spearkersSplittedColName] = CSV2RDF.__splitColumn(df[CSV2RDF.speakerColName])
        df[CSV2RDF.consultantSplittedColName] = CSV2RDF.__splitColumn(df[CSV2RDF.consultantColName])
        df[CSV2RDF.genreSplittedColName] = CSV2RDF.__splitColumn(df[CSV2RDF.genreColName])
        df[CSV2RDF.associatedPhotoColName] = df[CSV2RDF.associatedPhotoColName].apply(
            lambda x: str(x) if isinstance(x, float) else x)
        df[CSV2RDF.photoSplittedColName] = CSV2RDF.__splitColumn(df[CSV2RDF.associatedPhotoColName])
        df[CSV2RDF.languageSplittedColName] = CSV2RDF.__splitColumn(df[CSV2RDF.languageColName])
    
        df[CSV2RDF.parsedDateColName] = df[CSV2RDF.dateColName].apply(
            pd.to_datetime, format=self.datetimeformat)

        mediaRowSplitted = CSV2RDF.__splitColumn(df[CSV2RDF.mediaFileNameColName])
        df[CSV2RDF.mediaObjectColName] = CSV2RDF.__createRowMedia(mediaRowSplitted)

        self.df = df
 

    def __createRowMedia(mediaRowSplitted):
        timeSpanRe = re.compile('^([^{]+)(\{([^:]+):(.+)\})?$')
        lostRe     = re.compile(CSV2RDF.LOST_PREFIX)
        sessionRe  = re.compile(CSV2RDF.SESSION_PREFIX)
        res = [None] * len(mediaRowSplitted)
        for i, ms in enumerate(mediaRowSplitted):
            if ms == None:
                continue
            row = []
            for m in ms:
                if m.startswith(CSV2RDF.LOST_PREFIX): #lostRe.match(m):
                    row.append(LostReference(m.partition(CSV2RDF.LOST_PREFIX)[2]))
                elif m.startswith(CSV2RDF.SESSION_PREFIX): #sessionRe.match(m):
                    row.append(SessionReference(m.partition(CSV2RDF.SESSION_PREFIX)[2]))
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
        fieldtrip = df[CSV2RDF.fieldSessionIDColName].unique()
        fieldSessionMap = dict()
        for i, f in enumerate(fieldtrip):
            node = self.__createFieldSessionRdfNode(f)
            fieldSessionMap[f] = node
    
        # Create the Session events
        for i, row in df.iterrows():
            eventNodeURIRef = self.__createRDFEvent(
                row,
                df[CSV2RDF.spearkersSplittedColName][i],
                df[CSV2RDF.consultantSplittedColName][i],
                df[CSV2RDF.genreSplittedColName][i],
                df[CSV2RDF.photoSplittedColName][i],
                df[CSV2RDF.languageSplittedColName][i]
            )
    
            # Link between the event and the field session event
            self.g.add((fieldSessionMap[df[CSV2RDF.fieldSessionIDColName]
                  [i]], Ric4Fielddata.Rdf4Corpus.SubEvent, eventNodeURIRef))
    
            # Create the recording set if any
            mediaSourceSetURIRef = None
            if row[CSV2RDF.mediaObjectColName] is not None:
                mediaSourceSetURIRef = self.__createRDFMediaSourceSet(row[CSV2RDF.mediaObjectColName])
    
            # Create the reference to notebook if any
            notebookURIRef = None
            # volColName is the col used to test for MEDIA_AND_SESSION... use rather that one?
            if row[CSV2RDF.sessionIDColName] is not None:
                notebookURIRef = self.__createRDFNotebookRef(row)
    
            rowType = row[CSV2RDF.rowTypeColName]
    
            if rowType == CSV2RDF.COL_TYPE_MEDIA_ONLY_ROW:
                if row[CSV2RDF.mediaObjectColName] is None:
                    raise Exception("Media only row without media file: (row {i})")
                self.g.add((eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.Recording, mediaSourceSetURIRef))
    
            # Case 2: Session without media
            #         -> Go into EADFieldnote
            #         -> In Graph, WrittenDocument node. Link to EADFieldNote
            #         -> if Notes edges, do edges in Graph:
            #            if node -[transcription]-> link to target (Text type) with edge type = transcription
            #            if node -[comment]-> link to target (Text type) with edge type = comment
            #            if node -[stimulus]-> link from target (Text type) to StimulusID with edge type = stimulus
            #         -> if -[continuation]-> link the WrittenDocument to the WrittenDocument and the Text
            elif rowType == CSV2RDF.COL_TYPE_SESSION_ONLY_ROW:
                # FIXME what about the existing genre? should be erased
                self.g.add((eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.EventType,
                      Literal("DataSession", datatype=XSD.string)))
                self.g.add((eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.Product, notebookURIRef))
    
            # Case 3: session and media
            #         -> Make both case 2 and 3.
            #              note : Il ne peut pas y avoir deux fois "comment".
            #              note : il pourrait y avoir deux fois "stimulus"
            #         -> In Graph, link both node to Text node:
            #            NON if SessionID match "t" : WrittenDocument-[transcription]->text
            #            NON else: WrittenDocument-[notation]->text
            #            WrittenDocument-[transcription]->text
            #         -> if -[continuation]-> ERROR
            elif rowType == CSV2RDF.COL_TYPE_SESSION_AND_MEDIA_ROW:
    
                # There is BOTH a performance event and a datasession event
                # sometime the two are contiguous, sometime there is two different dates...
                # FIXME find the session associated with a recording belonging to another event
    
                # This gender is added to the existing gender of the first Event
                self.g.add((eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.EventType,
                      Literal("DataSession", datatype=XSD.string)))

                self.g.add((eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.Recording, mediaSourceSetURIRef))
                self.g.add((eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.Transcription, notebookURIRef))
    
            notes = None
            if row[CSV2RDF.notesColName] is not None:
                notes, freecomment = CSV2RDF.__parseNote(row[CSV2RDF.notesColName])
                if freecomment is not None:
                    for fc in freecomment:
                        # TODO may point to something else that the event...
                        self.g.add((eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.Comment,
                              Literal(fc, datatype=XSD.string)))
                if notes is not None:  # FIXME and if there is no note ???
                    if rowType == CSV2RDF.COL_TYPE_MEDIA_ONLY_ROW:
                        for n in notes:
                            if n[0] == "MentionInCahier":
                                # TODO may point to something else that the mediaSet?
                                # TODO how to link this to notebook?
                                self.g.add(
                                    (mediaSourceSetURIRef, Ric4Fielddata.Rdf4Corpus.Mention, Literal(n[1])))
                            else:
                                # TODO
                                # if note = comment or DataSessionRecording
                                # -> In Graph, Make a MediaDocument. Use the timestamp if present in the media file column
    
                                # Create the event pointed at in the structured note
    
                                # FIXME will correctly retrieve the thing?
                                # FIXME Should point to the Event, not the WrittenSource?
                                linkedSourceURIRef = URIRef(
                                    Ric4Fielddata.Rdf4CorpusVocabulary + Ric4Fielddata.URI_PREFIX_WrittenSource + n[1])
                                linkedEventURIRef = self.g.value(
                                    predicate=Ric4Fielddata.Rdf4Corpus.Transcription, object=linkedSourceURIRef)
                                if linkedEventURIRef is None:
                                    linkedEventURIRef = Literal("Not found!")
    
                                # Link to the event pointed at
    
                                if n[0] == "comment":
                                    self.g.add(
                                        (eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.Comment, linkedEventURIRef))
    
                                # It's only an Event "DataSession" that has a recording
                                # already stated in the "genre" field of this event
                                # Should indicate that this event is analyzing the target event
                                elif n[0] == "DataSessionRecording":
                                    self.g.add(
                                        (eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.Analyze, linkedEventURIRef))
                                else:
                                    raise Exception("Unknown case:" + n[0])
                    elif rowType == CSV2RDF.COL_TYPE_SESSION_ONLY_ROW:
                        for n in notes:
                            # FIXME duplicate code with just above
                            linkedSourceURIRef = URIRef(
                                Ric4Fielddata.Rdf4CorpusVocabulary + Ric4Fielddata.URI_PREFIX_WrittenSource + n[1])
                            # print(linkedSourceURIRef)
                            linkedEventURIRef = self.g.value(
                                predicate=Ric4Fielddata.Rdf4Corpus.Transcription, object=linkedSourceURIRef)
                            if linkedEventURIRef is None:
                                linkedEventURIRef = Literal("Not found!")
    
                            if n[0] == "comment":
                                self.g.add(
                                    (eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.Comment, linkedEventURIRef))
                            elif n[0] == "transcription":
                                self.g.add(
                                    (eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.Analyze, linkedEventURIRef))
                            elif n[0] == "continuation":
                                self.g.add(
                                    (eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.Continuation, linkedEventURIRef))
                            # Warning: here link from the context name.
                            # does not occurs in the data
                            # FIXME no need to linkedSourceURIRef to be created here
                            elif n[0] == "stimulus":
                                self.g.add((eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.Stimulus,
                                      Literal(n[1], datatype=XSD.string)))
                            else:
                                raise Exception("Unknown case:" + n[0])
                    elif rowType == CSV2RDF.COL_TYPE_SESSION_AND_MEDIA_ROW:
                        for n in notes:
                            if n[0] == "MentionInCahier":
                                self.g.add((eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.MentionInNotebook, Literal(
                                    n[1], datatype=XSD.string)))
                            elif n[0] == "stimulus":
                                self.g.add((eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.Stimulus,
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


    def __localizeMedia(self):
        """
        Localize in the filesystem the multimedia files and the session name.    
        """
    
        # get a 3-tuple of list of all files in media directory
        # get a list of file by sub-directory
        fileListList = []
        dirlist = []
        for dirname, subdirnames, filenames in os.walk(self.media_dir):
            fileListList.append(filenames)
            dirlist.append(dirname)

        # remove non-media file
        # mediaFileByDirListList = [[f for f in d if not re.search('session$|meta$|eaf$|pfsx$', f)] for d in fileListList]
        mediaFilePattern = [re.compile(mediaExt + "$") for mediaExt in self.mediaExts]
        mediaFileByDirListList = [
            [
                f for f in d if any(
                    [p.search(f) for p in mediaFilePattern]
                )
            ] for d in fileListList
        ]

        # create a dictionary of {filename -> directory}
        fullpathByFileName = dict()
        # create a dictionary of {basename -> directory}
        fullpathByBasedir = dict()
        for i in range(len(mediaFileByDirListList)):
            fullpath = dirlist[i]
            basedir = os.path.basename(fullpath)
            if basedir in fullpathByBasedir:
                raise Exception("duplicate session name: {basedir}")
            else:
                fullpathByBasedir[basedir] = fullpath
            for j in range(len(mediaFileByDirListList[i])):
                filename = mediaFileByDirListList[i][j]
                if filename in fullpathByFileName:
                    raise Exception("duplicate filename name: {filename}")
                else:
                    fullpathByFileName[filename] = fullpath

        self.fullpathByFileName = fullpathByFileName
        self.fullpathByBasedir = fullpathByBasedir


    def __populateMediaWithActualDirectory(self):
        rows = self.df[CSV2RDF.mediaObjectColName]
        for row in rows:
            if row == None:
                continue
            for media in row:
                if isinstance(media, FileNameReference):
                    parts = (media.name).split(".")
                    if (len(parts)) < 2:
                        raise Exception(f"{media.name} has no extension, object {media}.")
                    alternateSayMoreName = parts[0] + "_Source." + parts[1]
                    if media.name in self.fullpathByFileName:
                        media.setDir(self.fullpathByFileName[media.name])
                    elif alternateSayMoreName in self.fullpathByFileName:
                        media.setDir(self.fullpathByFileName[alternateSayMoreName])
                    else:
                        raise Exception(f"No localisation found of file {media.name}, object {media}.")
                elif isinstance(media, SessionReference):
                    media.setDir(self.fullpathByBasedir[media.name])


    def __getQualifiedSessionName(row):
        # TODO new rules in 2019
        if row[CSV2RDF.rowTypeColName] == CSV2RDF.COL_TYPE_MEDIA_ONLY_ROW:
            return None
        elif re.match('S', row[CSV2RDF.sessionIDColName]):
            return str(row[CSV2RDF.fieldSessionIDColName]) + '.' + str(row[CSV2RDF.volColName]) + '.' + row[CSV2RDF.sessionIDColName]
        else:
            return str(row[CSV2RDF.fieldSessionIDColName]) + row[CSV2RDF.sessionIDColName]


    def __getRowType(row):
        """Analyze the row and select between one of three type:
            - declare a multimedia event only
            - declare a fieldnote book session only
            - declare a fieldnote book session linked to an event"""
        if row[CSV2RDF.sessionIDColName] == None and row[CSV2RDF.mediaFileNameColName] != None:
            return CSV2RDF.COL_TYPE_MEDIA_ONLY_ROW
        elif row[CSV2RDF.sessionIDColName] != None and row[CSV2RDF.mediaFileNameColName] == None:
            return CSV2RDF.COL_TYPE_SESSION_ONLY_ROW
        elif row[CSV2RDF.sessionIDColName] != None and row[CSV2RDF.mediaFileNameColName] != None:
            return CSV2RDF.COL_TYPE_SESSION_AND_MEDIA_ROW
        # row[CSV2RDF.fieldSessionIDColName].match(r'Le |Lundi|Mardi|Mercredi|Jeudi|Vendredi|Samedi|Dimanche'):
        elif row[CSV2RDF.fieldSessionIDColName] != None and type(row[CSV2RDF.fieldSessionIDColName]) is str:
            return CSV2RDF.COL_TYPE_NEW_DATE_ROW
        else:
            print(f"Unknown case: {str(row)}")
            return 0


    def __createFieldSessionRdfNode(self, fieldsessionname):
        # warning : fieldsessionname is an int (converted while reading the data frame)
        mName = str(uuid.uuid4())
        fieldSessionNodeURIRef = URIRef(
            Ric4Fielddata.Rdf4CorpusVocabulary + Ric4Fielddata.URI_PREFIX_FieldSession + mName)
        self.g.add((fieldSessionNodeURIRef, RDF.type, Ric4Fielddata.Rdf4Corpus.Event))
        self.g.add((fieldSessionNodeURIRef, Ric4Fielddata.Rdf4Corpus.EventType,
              Literal(Ric4Fielddata.FieldSessionEventType, datatype=XSD.string)))
        self.g.add((fieldSessionNodeURIRef, Ric4Fielddata.Rdf4Corpus.FieldSessionName,
              Literal(str(fieldsessionname), datatype=XSD.string)))
        return fieldSessionNodeURIRef


    def __createRDFEvent(self, row, speakers, consultants, genres, photos, languages):
        mName = str(uuid.uuid4())
        eventNodeURIRef = URIRef(Ric4Fielddata.Rdf4CorpusVocabulary + Ric4Fielddata.URI_PREFIX_Event + mName)
        self.g.add((eventNodeURIRef, RDF.type, Ric4Fielddata.Rdf4Corpus.Event))
        self.g.add((eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.Date, Literal(
            row[CSV2RDF.parsedDateColName], datatype=XSD.date)))

        self.__addMultipleObject(eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.EventType,  genres)
        self.__addMultipleObject(eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.Language,   languages)
        self.__addMultipleObject(eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.Speaker,    speakers)
        self.__addMultipleObject(eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.Consultant, consultants)
        self.__addMultipleObject(eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.Photo,      photos)

        self.g.add((eventNodeURIRef, Ric4Fielddata.Rdf4Corpus.Title, Literal(
            row[CSV2RDF.descriptionColName], datatype=XSD.string)))
        return eventNodeURIRef


    def __addMultipleObject(self, subject, predicate, objects):
        if objects is not None:
            for o in objects:
                self.g.add((subject, predicate,
                      Literal(o, datatype=XSD.string)))


    def __createRDFMediaSourceSet(self, medias):
        """
        a MediaSourceSet point to one or more MediaRef :
    
        a Ric4Fielddata.Rdf4Corpus.MediaSourceSet----[Ric4Fielddata.Rdf4Corpus.MediaSource]----->a Ric4Fielddata.Rdf4Corpus.MediaRef
    
        a media ref holds the physical information:
    
        a Ric4Fielddata.Rdf4Corpus.MediaRef----[Ric4Fielddata.Rdf4Corpus.FileName]--->Literal(file URI)
                             ----[Ric4Fielddata.Rdf4Corpus.DirName]--->Literal(dir URI)
                             ----[Ric4Fielddata.Rdf4Corpus.StartSpan]--->Literal(dir URI)
                             ----[Ric4Fielddata.Rdf4Corpus.EndSpan]--->Literal(dir URI)
    
        """
        mName = str(uuid.uuid4())
        mediaSourceSet = URIRef(Ric4Fielddata.Rdf4CorpusVocabulary +
                                Ric4Fielddata.URI_PREFIX_MediaSourceSet + mName)
        self.g.add((mediaSourceSet, RDF.type, Ric4Fielddata.Rdf4Corpus.MediaSourceSet))
        for m in medias:
            media = URIRef(
                Ric4Fielddata.Rdf4CorpusVocabulary + Ric4Fielddata.URI_PREFIX_MediaReference + mName + ":" + m.name)
            self.g.add((media, RDF.type, Ric4Fielddata.Rdf4Corpus.MediaRef))
            self.g.add((mediaSourceSet, Ric4Fielddata.Rdf4Corpus.MediaSource, media))
            self.g.add((media, Ric4Fielddata.Rdf4Corpus.FileName,
                  Literal(m.name, datatype=XSD.anyURI)))
            if isinstance(m, LocalizedMediaReference):
                self.g.add((media, Ric4Fielddata.Rdf4Corpus.DirName, Literal(m.dir, datatype=XSD.anyURI)))
            #g.add((mediaRefNodeName, Ric4Fielddata.Rdf4Corpus.MediaScene, Literal(localized_media[0][0])))
            # FIXME Could in theory appears for each file, but in practice only on length-1 set
            if isinstance(m, FileNameReference) and m.getTimestamp():
                self.g.add((media, Ric4Fielddata.Rdf4Corpus.StartSpan,
                      Literal(m.start_timestamp, datatype=XSD.string)))
                self.g.add((media, Ric4Fielddata.Rdf4Corpus.EndSpan,
                      Literal(m.end_timestamp, datatype=XSD.string)))
        return mediaSourceSet
    
    
    def __createRDFNotebookRef(self, row):
        qName = row[CSV2RDF.qualifiedSessionNameColName]
        if qName is None:
            qName = Ric4Fielddata.Missing
        notebookURIRef = URIRef(Ric4Fielddata.Rdf4CorpusVocabulary +
                                Ric4Fielddata.URI_PREFIX_WrittenSource + qName)
        self.g.add((notebookURIRef, RDF.type, Ric4Fielddata.Rdf4Corpus.NotebookRef))
        self.g.add((notebookURIRef, Ric4Fielddata.Rdf4Corpus.qualifiedName,
              Literal(qName, datatype=XSD.anyURI)))
        self.g.add((notebookURIRef, Ric4Fielddata.Rdf4Corpus.NotebookVol,
              Literal(row[CSV2RDF.volColName], datatype=XSD.anyURI)))
        self.g.add((notebookURIRef, Ric4Fielddata.Rdf4Corpus.NotebookPage, Literal(
            row[CSV2RDF.pageNumberColName], datatype=XSD.anyURI)))
        self.g.add((notebookURIRef, Ric4Fielddata.Rdf4Corpus.otherFlexComText, Literal("")))
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

    def getTimestamp(self):
        return self.hasTimestamp
    

class SessionReference(LocalizedMediaReference):
    pass

