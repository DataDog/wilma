import os
from pathlib import Path

import pytest

from wilma._config import WilmaConfig


def test_wilmafile_cwd(tmp_path):
    wilmafile = tmp_path / WilmaConfig.wilmafile.default.name
    wilmafile.write_text("imports = []")

    cwd = Path.cwd()
    os.chdir(tmp_path)

    assert WilmaConfig().wilmafile == WilmaConfig.wilmafile.default

    os.chdir(cwd)


def test_get_path_env_invalid_file(monkeypatch):
    monkeypatch.setenv("WILMAFILE", os.path.join("foo", "bar.yaml"))

    c = WilmaConfig()
    assert not c.wilmafile.exists()
    assert c.wilmaconfig == {}


def test_get_path_env_valid_file(monkeypatch, tmp_path):
    wilmafile = tmp_path / WilmaConfig.wilmafile.default.name
    wilmafile.write_text("imports = []")
    monkeypatch.setenv("WILMAFILE", str(wilmafile))

    assert WilmaConfig().wilmafile == wilmafile


def test_load(monkeypatch, tmp_path):
    wilmafile = tmp_path / WilmaConfig.wilmafile.default
    wilmafile.write_text("imports = []")
    monkeypatch.setenv("WILMAFILE", str(wilmafile))

    assert WilmaConfig().wilmaconfig == {"imports": []}
