import sys
from pathlib import Path
from subprocess import PIPE
from subprocess import check_output


HERE = Path(__file__).parent


def test_probe_main():
    result = check_output(
        ["wilma", sys.executable, "-m", "target"],
        stderr=PIPE,
        cwd=str(HERE),
    )

    assert (
        result
        == b"""I'm not telling you the secret!
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
            "wilma",
            "-c",
            str(HERE / "tools" / "locals.toml"),
            sys.executable,
            "-m",
            "target",
        ],
        stderr=PIPE,
        cwd=str(HERE),
    ).decode()

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
            "wilma",
            "-c",
            str(HERE / "tools" / "framestack.toml"),
            sys.executable,
            "-m",
            "target",
        ],
        stderr=PIPE,
        cwd=str(HERE),
    ).decode()

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
