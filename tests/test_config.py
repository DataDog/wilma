import os

from wilma._config import WILMAFILE_NAME, get_path, load


def test_get_path_cwd(tmp_path):
    wilmafile = tmp_path / WILMAFILE_NAME
    wilmafile.write_text("imports = []")

    cwd = os.getcwd()
    os.chdir(tmp_path)

    assert get_path() == os.path.join(os.getcwd(), WILMAFILE_NAME)

    os.chdir(cwd)


def test_get_path_env_invalid_file(monkeypatch):
    monkeypatch.setenv("_WILMAFILE", os.path.join("foo", "bar.yaml"))

    assert get_path() is None


def test_get_path_env_valid_file(monkeypatch, tmp_path):
    wilmafile = tmp_path / WILMAFILE_NAME
    wilmafile.write_text("imports = []")
    monkeypatch.setenv("_WILMAFILE", str(wilmafile))

    assert get_path() == str(wilmafile)


def test_load(monkeypatch, tmp_path):
    wilmafile = tmp_path / WILMAFILE_NAME
    wilmafile.write_text("imports = []")
    monkeypatch.setenv("_WILMAFILE", str(wilmafile))

    assert load(get_path()) == {"imports": []}
