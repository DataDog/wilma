import os
import typing as t

import toml

WILMAFILE_NAME = "wilma.toml"


def get_path():
    # type: () -> t.Optional[str]
    """Determine the path of the Wilma file.

    Returns ``None`` if the file was not found."""
    path = os.getenv("_WILMAFILE") or os.path.join(os.getcwd(), WILMAFILE_NAME)
    return path if os.path.isfile(path) else None


load = toml.load  # TODO: Expand to do validation
