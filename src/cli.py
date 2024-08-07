import argparse
import sys
from rdflib import Graph, RDF, URIRef
from rdf4lfd.parse_lameta import Lameta2RdfParser
from rdf4lfd.parse_spreadsheet import Spreadsheet2RDF
from rdf4lfd.converter import Converter
from rdf4lfd.parse_directory import ConvertDirectoryIntoRicRdf
from rdf4lfd.fielddata_namespace import FieldDataNS
from rdf4lfd.rico_namespace import RICO

def _print_detail(g:Graph) -> None:
    print(f"Size of the graph: {len(g)}")
    _print_type(g, RICO.Event, "event")
    _print_type(g, RICO.Record, "record")

def _print_type(g:Graph, type:URIRef, type_name:str) -> None:
    objs = list(g.triples((None, RDF.type, type)))
    print(f"{len(objs)} {type_name}(s) found:")
    for s, p, o in objs:
        for s2, p2, o2 in g.triples((s, FieldDataNS.BaseName, None)):
            print(f"\t{o2}")

def _run_parser(parser:Converter, arg) -> None:
    parser.convert()
    g:Graph = parser.get_graph()
    g.serialize(destination=arg.output, format=arg.out_format)
    if arg.verbose:
        _print_detail(g)
    print("Conversion completed")

def parse_directories_callback(arg):
    parser = ConvertDirectoryIntoRicRdf(corpus_uri_prefix=arg.corpus_prefix, extensions=arg.extensions, directory=arg.input_dir)
    _run_parser(parser, arg)

def parse_spreadsheet_callback(arg):
    parser = Spreadsheet2RDF(file=arg.input, format=arg.in_format, sheet_index=arg.sheet, conf_file=arg.conf, context_graph_file=arg.context, corpus_uri_prefix=arg.corpus_prefix)
    _run_parser(parser, arg)

def parse_lameta_callback(arg):
    parser = Lameta2RdfParser(arg.input_dir, corpus_uri_prefix=arg.corpus_prefix)
    _run_parser(parser, arg)

def aggregate_callback(arg):
    pass #Aggregated(arg.graph)

def create_callback(arg):
    pass #Aggregated(arg.graph)

def run_cli():
    # Main level
    parser = argparse.ArgumentParser(description='Managing linguistic field data with RDF.')
    parser.add_argument('--verbose', '-v', help='output detailled information', required=False, action='store_true')
    command_subparser = parser.add_subparsers(title="subcommand", description="one valid subcommand", help='subcommand: the main action to run. See subcommand -h for more info', required=True)

    ## create subcommand
    create_parser = command_subparser.add_parser('create', help='aggregate data sources')
    create_parser.add_argument('--graph', '-g', help='file containing the aggregated RDF data', required=True, type=str)
    create_parser.set_defaults(func=create_callback)

    ## update or add subcommand
    aggregate_parser = command_subparser.add_parser('aggr', help='aggregate (add or update) a data sources to an aggregated graph')
    aggregate_parser.add_argument('--graph', '-g', help='file containing the aggregated RDF data', required=True, type=str)
    aggregate_parser.add_argument('--subgraph', '-s', help='file containing the data to be added or updated', required=True, type=str)
    aggregate_parser.add_argument('--iri', '-i', help='subgraph IRI', required=True, type=str)
    aggregate_parser.set_defaults(func=aggregate_callback)

    ## convert subcommand
    convert_parser = command_subparser.add_parser('convert', help='convert data into rdf')
    convert_parser.add_argument('--output', '-o', help='output file for the RDF serialization', required=True, type=str)
    convert_parser.add_argument('--out_format', '-of', help='format for the RDF serialization', required=False, choices=["turtle", "xml", "n3"], default="turtle", type=str)
    convert_parser.add_argument('--corpus_prefix', '-p', help='prefix for creating URI of events, records and other objects describing the corpus', required=False, default="http://mycorpus/com/", type=str)
    convert_parser.add_argument('--context_graph', '-g', help='graph containing already defined resources to lookup and to refer to', required=False, type=str)

    convert_format_subparser = convert_parser.add_subparsers(title="format", description="one valid subcommand:", help='data source format to be converted. See -h for more info', required=True)

    # directory
    directories_parser = convert_format_subparser.add_parser('directories', help='convert a list of subdirectories into a set of Event containing Record and Instance using RIC-RDF')
    directories_parser.add_argument('--input_dir', '-i', help='parent directory to be analyzed', required=True, type=str)
    directories_parser.add_argument('--extensions', '-e', help='whitespace separated list of extensions for filtering files', required=False, type=str, nargs='+')
    directories_parser.set_defaults(func=parse_directories_callback)

    # lameta
    lameta_parser = convert_format_subparser.add_parser('lameta', help='convert lameta database into RIC-RDF')
    lameta_parser.add_argument('--input_dir', '-i', help='root directory of a lameta project', required=True, type=str)
    lameta_parser.set_defaults(func=parse_lameta_callback)

    # spreadsheet
    spreadsheet_parser = convert_format_subparser.add_parser('spreadsheet', help='convert spreadsheet into RIC-RDF')
    spreadsheet_parser.add_argument('--input', '-i', help='path to a spreadsheet', required=True, type=str)
    spreadsheet_parser.add_argument('--in_format', '-if', help='spreadsheet format', required=False, choices=["ODT", "CSV"], default="ODT", type=str)
    spreadsheet_parser.add_argument('--conf', '-c', help='a json files describing the data in the spreadsheet', required=True, type=str)
    spreadsheet_parser.add_argument('--sheet', '-s', help='index of the sheet to be read', required=False, type=int, default=1)
    spreadsheet_parser.set_defaults(func=parse_spreadsheet_callback)

    if len(sys.argv) <= 1:
        sys.argv.append('-h')
    if len(sys.argv) == 2 and sys.argv[1] == "convert":
        sys.argv.append('-h')
    argument = parser.parse_args()

    argument.func(argument)
