import atexit
import logging
import os
import sys
from contextlib import contextmanager

import run_module  # noqa
from ddtrace.debugging._debugger import DebuggerModuleWatchdog

from wilma._config import wilmaenv
from wilma._inject import on_config_changed


LOGGER = logging.getLogger(__name__)


@contextmanager
def cwd():
    sys.path.insert(0, os.getcwd())
    try:
        yield
    finally:
        sys.path.pop(0)


class WilmaException(Exception):
    pass


try:
    # Set verbosity level
    if wilmaenv.verbose:
        logging.basicConfig(level=logging.INFO)

    # Install module watchdog
    try:
        DebuggerModuleWatchdog.install()
    except RuntimeError:
        pass
    atexit.register(DebuggerModuleWatchdog.uninstall)

    # Create the Wilma prefix directory
    wilmaenv.wilmaprefix.mkdir(exist_ok=True)

    # Listen for changes to the Wilma file
    wilmaenv.observe(on_config_changed)

    # Initial configuration
    on_config_changed(wilmaenv.wilmaconfig)


except WilmaException:
    pass
