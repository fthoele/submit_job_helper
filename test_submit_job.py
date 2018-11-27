import pytest
import tempfile

import submit_job

def check_output_mock(*args, **kwargs):
    return b"Job <1234> is submitted to queue <normal.120h>."

def check_output_daint_mock(*args, **kwargs):
    return b"Submitted batch job 1234"

@pytest.fixture
def setup(mocker):
    args = ["", "jobscript"]
    mocker.patch("sys.argv", args)
    mocker.patch("subprocess.check_output", check_output_mock)


def test_run(setup, capsys):
    with tempfile.TemporaryFile(mode="a+") as fp:
        submit_job.run(submit_job.EulerJobRunner, fp)

        fp.seek(0)
        result = fp.read()
        words = result.split()
        assert words[2] == "1234"
        assert words[4] == "jobscript"
        assert words[5] == "jobname"

        captured = capsys.readouterr()
        assert captured.out == "Job <1234> is submitted to queue <normal.120h>.\n"


def test_run_2(mocker):
    args = ["", "jobscript", "jobscript_2"]
    mocker.patch("sys.argv", args)
    mocker.patch("subprocess.check_output", check_output_mock)

    with tempfile.TemporaryFile(mode="a+") as fp:
        submit_job.run(submit_job.EulerJobRunner, fp)

        fp.seek(0)
        lines = fp.readlines()
        
        words = lines[0].split()
        assert words[2] == "1234"
        assert words[4] == "jobscript"
        assert words[5] == "jobname"

        words = lines[1].split()
        assert words[2] == "1234"
        assert words[4] == "jobscript_2"
        assert words[5] == "jobname_2"


def test_invalid_filename(mocker, capsys):
    args = ["", "invalid_filename"]
    mocker.patch("sys.argv", args)
    mocker.patch("subprocess.check_output", check_output_mock)

    with tempfile.TemporaryFile(mode="a+") as fp:
        submit_job.run(submit_job.EulerJobRunner, fp)
        captured = capsys.readouterr()
        assert captured.out == "[Errno 2] No such file or directory: 'invalid_filename'\n"



def test_daint(mocker, capsys):
    args = ["", "jobscript_daint"]
    mocker.patch("sys.argv", args)
    mocker.patch("subprocess.check_output", check_output_daint_mock)

    with tempfile.TemporaryFile(mode="a+") as fp:
        submit_job.run(submit_job.DaintJobRunner, fp)
        captured = capsys.readouterr()
        assert captured.out == "Submitted batch job 1234\n"

        fp.seek(0)
        result = fp.read()
        words = result.split()
        assert words[2] == "1234"
        assert words[4] == "jobscript_daint"
        assert words[5] == "jobname"