import atexit
import logging
import os
import site
import sys
from contextlib import contextmanager
from pathlib import Path
from subprocess import check_output


LOGGER = logging.getLogger(__name__)

WILMAPREFIX = Path(os.getenv("WILMAPREFIX", ".wilma"))
DEPS = WILMAPREFIX / "deps"
if not DEPS.exists():
    # Install Wilma dependencies in isolation
    dependencies = [
        "ddtrace~=1.9",
        "toml~=0.10.2",
        "envier~=0.4",
        "bytecode~=0.13.0; python_version<'3.8'",
        "bytecode~=0.14.0; python_version>='3.8'",
        "watchdog~=2.1.9",
    ]
    try:
        env = dict(os.environ)

        # Create a virtual environment to completely isolate Wilma's
        # dependencies.
        env["PYTHONPATH"] = ""
        check_output(
            [sys.executable, "-m", "venv", str(DEPS.resolve())],
            env=env,
        )
        check_output(
            [
                str(DEPS / "bin" / "python"),
                "-m",
                "pip",
                "install",
                "--prefix",
                str(DEPS.resolve()),
                "--no-input",
                "--no-python-version-warning",
            ]
            + dependencies,
            env=env,
        )
    except Exception:
        LOGGER.error("Failed to install dependencies", exc_info=True)
        raise

# Add Wilma dependencies to the path
wilma_deps = site.getsitepackages(prefixes=[str(DEPS.resolve())])
sys.path[0:0] = wilma_deps

import wilma._bootstrap.run_module  # noqa
from wilma._config import wilmaenv
from wilma._inject import WilmaModuleWatchdog
from wilma._inject import on_config_changed


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
        WilmaModuleWatchdog.install()
    except RuntimeError:
        pass
    atexit.register(WilmaModuleWatchdog.uninstall)

    # Create the Wilma prefix directory
    wilmaenv.wilmaprefix.mkdir(exist_ok=True)

    # Listen for changes to the Wilma file
    wilmaenv.observe(on_config_changed)

    # Initial configuration
    on_config_changed(wilmaenv.wilmaconfig)

except WilmaException:
    LOGGER.error("Cannot initialise Wilma", exc_info=True)

# Remove Wilma dependencies from the path
sys.path[: len(wilma_deps)] = []
