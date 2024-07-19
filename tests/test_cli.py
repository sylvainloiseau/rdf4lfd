from cli import run_cli
import pytest
import sys
import os

@pytest.mark.parametrize("option", ("", "-h", "--help"))
def test_help(capsys, option):
    try:
        sys.argv = [option]
        run_cli()
    except SystemExit:
        pass
    output = capsys.readouterr().out
    assert 'Managing linguistic field data with RDF.' in output

def test_parsedirectory(capsys, tmp_path):
    try:
        sys.argv = ["rdflfd", "convert", "--output=" + str(tmp_path / "test.turtle"), "directories", "--input_dir=sample/data/SayMoreProjects/Test/Sessions"]
        print(sys.argv)
        run_cli()
    except SystemExit:
        pass
    output = capsys.readouterr().out
    assert "Conversion completed" in output

def test_parse_lameta(capsys, tmp_path, request):
    directory = os.path.join(os.path.dirname(request.path), '../sample/data/SayMoreProjects/Test')
    try:
        sys.argv = ["rdflfd", "convert", "--output=" + str(tmp_path / "test.turtle"), "lameta", "--input_dir=" + directory]
        print(sys.argv)
        run_cli()
    except SystemExit:
        pass
    output = capsys.readouterr().out
    assert "Conversion completed" in output