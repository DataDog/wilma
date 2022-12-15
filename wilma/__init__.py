import pkg_resources

from wilma._tools import framestack
from wilma._tools import locals
from wilma._tools import capture
from wilma._tools import watch


try:
    __version__ = pkg_resources.get_distribution(__name__).version
except pkg_resources.DistributionNotFound:
    __version__ = "dev"


__all__ = ["framestack", "locals", "capture", "watch"]
