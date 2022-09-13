import argparse
import sys
from saymore import SayMore2RdfParser
from csv import CSV2RDF

# https://stackoverflow.com/questions/56534678/how-to-create-a-cli-in-python-that-can-be-installed-with-pip
# https://docs.python.org/3/library/argparse.html#the-add-argument-method

def import_csv_callback(arg, backup_conf):
    parser = CSV2RDF()
    parser.convert()

def import_lameta_callback(arg, backup_conf):
    sm = SayMore2RdfParser(arg.input)
    sm.parse()
    sm.graph.serialize(destination=arg.output)
#     s = backup_conf.get_schemes()
#     table = pd.DataFrame.from_dict(s).transpose()
#         # df = pd.DataFrame(
#         # columns=['Age', 'Birth City', 'Gender'],
#         # index=['Jane', 'Melissa', 'John', 'Matt'])
#     if arg.group == "source":
#         by_source = table.groupby('source')
#         print(by_source)
#         #print(by_source.describe())
#         for key, item in by_source:
#           print(by_source.get_group(key), "\n\n")
#     elif arg.group == "target":
#         print(table.groupby('target_disk'))
#     elif arg.full:
#         print(table)
#     else:
#         [print(k) for k in list(s.keys())]

def cli():
    # Main level
    parser = argparse.ArgumentParser(description='Helpers tools for managing field data with RIC-RDF. See Record in context.')
    subparsers = parser.add_subparsers(title="subcommand", description="one valid subcommand", help='subcommand: the main action to run. See subcommand -h for more info', required=True)

    ## convert subcommand
    parser_list = subparsers.add_parser('convert', help='convert data into rdf')
    parser_list.add_argument('--output', '-o', help='group scheme by source or target', required=True)

    parser_list_subparser = parser_list.add_subparsers(title="format", description="data source format", help='data source format, as produced by a given app. See -h for more info', required=True)

    # lameta
    parser_list_lameta = parser_list_subparser.add_parser('lameta', help='convert lameta database into RIC-RDF')
    parser_list_lameta.add_argument('--full', '-f', help='all available information for each scheme', required=False, action='store_true')
    parser_list_lameta.add_argument('--input', '-i', help='Input directory of a lameta', required=False, action='store_true')
    parser_list_lameta.set_defaults(func=import_lameta_callback)

    # CSV
    parser_list_csv = parser_list_subparser.add_parser('lameta', help='convert lameta database into RIC-RDF')
    parser_list_csv.add_argument('--full', '-f', help='all available information for each scheme', required=False, action='store_true')
    parser_list_csv.add_argument('--input', '-i', help='Input directory of a lameta', required=False, action='store_true')
    parser_list_csv.set_defaults(func=import_csv_callback)


    if len(sys.argv) <= 1:
        sys.argv.append('-h')
    argument = parser.parse_args()

    argument.func(argument)

    # exec(open("backup.py").read())
                                       