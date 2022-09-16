import typing as t
from pathlib import Path

import toml
from envier import En


def validate_wilmafile(wilmafile: Path) -> None:
    if not wilmafile.exists():
        raise ValueError("No Wilma file found.")


class WilmaConfig(En):
    wilmafile = En.v(
        Path,
        "wilmafile",
        validator=validate_wilmafile,
        default=Path("wilma.toml"),
    )

    wilmaprefix = En.v(
        Path,
        "wilmaprefix",
        default=Path(".wilma"),
    )

    venv = En.v(
        t.Optional[Path],
        "virtual_env",
        default=None,
    )

    wilmaconfig = En.d(dict, lambda c: toml.loads(c.wilmafile.read_text()))
    metadata_path = En.d(Path, lambda c: c.wilmaprefix / "metadata.json")
