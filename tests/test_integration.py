from subprocess import PIPE, check_output

from wilma._config import WILMAFILE_NAME


def test_probe_main(tmp_path):
    test_script = tmp_path / "test.py"
    test_script.write_text(
        """
def foo(secret):
    print("I'm not telling you the secret!")
    return None


foo("Wilma rox!")
"""
    )

    wilmafile = tmp_path / WILMAFILE_NAME
    wilmafile.write_text(
        """
[probes]
"test.py:4" = "print('secret =', secret)"
"""
    )

    assert (
        check_output(["wilma", "python", "-m", "test"], stderr=PIPE, cwd=str(tmp_path))
        == b"I'm not telling you the secret!\nsecret = Wilma rox!\n"
    )
