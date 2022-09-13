from rdffielddata.parse_directory import ConvertDirectoryIntoRicRdf
import os

class TestConvertDirectoryIntoRicRdf:

    @staticmethod
    def test_parse_directory(request):
        directory = os.path.join(os.path.dirname(request.path), '../sample/data/SayMoreProjects/Test/Sessions')
        parser = ConvertDirectoryIntoRicRdf(
            project_prefix="http://mycorpus",
            directory=directory,
            extensions=[".MOV", ".WAV", ".MTS", ".wav", ".wma"],
            graph_identifier="directory",
            directoryhook=None,
            filesethook=None,
            filehook=None
        )
        g = parser.get_graph()
        print(len(g))
        for s, p, o in g:
            print(f"{s},{p},{o}")
        for s, p, o in g:
            print(f"{s},{p},{o}")

