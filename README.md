RDF4LFD : RDF for linguistic fieldwork data

# Installation

```
pip install git+https://github.com/sylvainloiseau/rdfFieldData#egg=rdffielddata
```

# Usage

```
rdflfd --help
```

# Description

Main functions provided:

- convert a set of subdirectories containing various files into a RDF base of Event (=subdirectories) associated with Record and Instance (= files)
- Convert a SIL SayMore/Lameta project into an RDF base (all xml files (project, people, session) as well as files structures and file metadata (```*.meta``` file)
- Convert a spreadsheet (CSV, ODS) containing additional informations (such as relations between sessions, documents and transcriptions) into RDF.

The RDF vocabulary used is [Record in context Conceptual Model 0.2 (RiC-CM 0.2)](https://www.ica.org/sites/default/files/ric-cm-02_july2021_0.pdf) by the [International Council on Archives](https://www.ica.org/en)

# Development

Run a single test:

```
tox -epy310 -- -k test_get_subgraphes
```

Run tests creating resources (skipped otherwise) in sample/data:

```
tox -epy310 -- --create_resources -k test_creating_resources
```
