import atexit
import json
import logging
import os
import sys
from contextlib import contextmanager
from pathlib import Path

import run_module  # noqa
from ddtrace.debugging._debugger import DebuggerModuleWatchdog

from wilma._config import wilmaenv
from wilma._inject import on_config_changed
from wilma._tools import registerCaptureOutput


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


class FileAppender(object):
    def __init__(self, path:Path):
        self.path = path
        self.stream = self.path.open("a")

    def __call__(self, capture):
        self.stream.write(json.dumps(capture) + "\n")

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

    # Register capture output
    registerCaptureOutput(FileAppender(wilmaenv.captures_path))

    # Listen for changes to the Wilma file
    wilmaenv.observe(on_config_changed)

    # Initial configuration
    on_config_changed(wilmaenv.wilmaconfig)


except WilmaException:
    pass
