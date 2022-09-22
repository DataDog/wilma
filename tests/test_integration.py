import sys
from pathlib import Path
from subprocess import PIPE
from subprocess import check_output


def test_probe_main():
    result = check_output(
        ["wilma", sys.executable, "-m", "target"],
        stderr=PIPE,
        cwd=str(Path(__file__).parent),
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
        ["wilma", "-c", "tools.toml", sys.executable, "-m", "target"],
        stderr=PIPE,
        cwd=str(Path(__file__).parent),
    )

    assert (
        result
        == b"""I'm not telling you the secret!
secret="new secret"
I'm not telling you the class secret!
I'm not telling you the imported secret!
I'm not telling you the imported class secret!
"""
    ), result
