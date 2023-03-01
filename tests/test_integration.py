import sys
from pathlib import Path
from subprocess import PIPE
from subprocess import check_output as _check_output
from threading import Thread
from time import sleep


HERE = Path(__file__).parent
EXE = "wilma.exe" if sys.platform == "win32" else "wilma"


def check_output(*args, **kwargs):
    return _check_output(*args, **kwargs).replace(b"\r", b"").decode()


def test_probe_main():
    result = check_output(
        [EXE, sys.executable, "-m", "target"],
        stderr=PIPE,
        cwd=str(HERE),
    )

    assert (
        result
        == """I'm not telling you the secret!
secret="Wilma rox!"
I'm not telling you the class secret!
class secret="I'm a class secret!"
I'm not telling you the imported secret!
imported secret="I'm an imported secret!"
I'm not telling you the imported class secret!
imported class secret="I'm an imported class secret!"
"""
    ), result


def test_tools_locals():
    result = check_output(
        [
            EXE,
            "-c",
            str(HERE / "tools" / "locals.toml"),
            sys.executable,
            "-m",
            "target",
        ],
        stderr=PIPE,
        cwd=str(HERE),
    )

    assert (
        result
        == """I'm not telling you the secret!
secret="new secret"
I'm not telling you the class secret!
I'm not telling you the imported secret!
I'm not telling you the imported class secret!
"""
    ), result


def test_tools_framestack():
    result = check_output(
        [
            EXE,
            "-c",
            str(HERE / "tools" / "framestack.toml"),
            sys.executable,
            "-m",
            "target",
        ],
        stderr=PIPE,
        cwd=str(HERE),
    )

    for line in (
        "line 5, in foo (top-most frame last)",
        ", in _run_module_as_main",
        ", in _wrapped_run_code",
        ", in _run_code",
        ", line 17, in <module>",
    ):
        assert line in result, result

    assert result.endswith(
        """    foo("Wilma rox!")
Hello framestack
I'm not telling you the secret!
I'm not telling you the class secret!
I'm not telling you the imported secret!
I'm not telling you the imported class secret!
"""
    ), result


def test_wilmafile_watch(tmp_path):
    wilmafile_content = (HERE / "watch.toml").read_text()
    wilmafile = tmp_path / "watch.toml"
    wilmafile.write_text(wilmafile_content)

    writer = Thread(
        target=lambda: sleep(1)
        or wilmafile.write_text(wilmafile_content.replace("foo", "bar"))
    )
    writer.start()

    result = check_output(
        [
            EXE,
            "-c",
            str(wilmafile),
            sys.executable,
            "-m",
            "target_watch",
        ],
        stderr=PIPE,
        cwd=str(HERE),
    )

    writer.join()

    assert "foo" in result and "bar" in result, result
