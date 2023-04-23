import sys
from pathlib import Path

import pkg_resources


# Determine if we are preloading Wilma. We expect dependencies to be available
# in this case.
PRELOAD = False

frame = sys._getframe()
while frame:
    if Path(frame.f_code.co_filename).name == "preload.py":
        PRELOAD = True
        break
    frame = frame.f_back

try:
    from wilma._tools import capture
    from wilma._tools import framestack
    from wilma._tools import locals
    from wilma._tools import watch

    __all__ = ["framestack", "locals", "capture", "watch"]

except ImportError as e:
    if PRELOAD:
        raise

try:
    __version__ = pkg_resources.get_distribution(__name__).version
except pkg_resources.DistributionNotFound:
    __version__ = "dev"
