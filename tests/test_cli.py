from rdf4lfd.cli import cli
import pytest
import sys

@pytest.mark.parametrize("option", ("", "-h", "--help"))
def test_help(capsys, option):
    try:
        sys.argv = [option]
        cli()
    except SystemExit:
        pass
    output = capsys.readouterr().out
    assert "Helpers tools for managing field data with RIC-RDF" in output

def test_parsedirectory(capsys, tmp_path):
    try:
        sys.argv = ["rdflfd", "convert", "--output=" + str(tmp_path / "test.turtle"), "directories", "--input_dir=sample/data/SayMoreProjects/Test/Sessions"]
        print(sys.argv)
        cli()
    except SystemExit:
        pass
    output = capsys.readouterr().out
    assert "Conversion completed" in output