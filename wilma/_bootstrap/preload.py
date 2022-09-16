import atexit
import json
import logging
import os
import site
import sys
from contextlib import contextmanager
from subprocess import check_output

import run_module  # noqa
from ddtrace.internal.module import ModuleWatchdog

from wilma._config import WilmaConfig
from wilma._inject import Probe
from wilma._inject import on_import


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
    wilmaenv = WilmaConfig()
    if wilmaenv.verbose:
        logging.basicConfig(level=logging.INFO)
    wilmaenv.wilmaprefix.mkdir(exist_ok=True)

    config = wilmaenv.wilmaconfig

    LOGGER.info("Reading metadata ...")
    metadata = (
        json.loads(wilmaenv.metadata_path.read_text())
        if wilmaenv.metadata_path.exists()
        else {}
    )

    # Install dependencies in prefix
    deps = {
        f"{p}{v.replace('latest', '')}"
        for p, v in config.get("dependencies", {}).items()
    }
    installed_deps = set(metadata.get("dependencies", []))
    new_deps = list(deps - installed_deps)

    if new_deps:
        LOGGER.info("Installing new dependencies: %s", new_deps)
        pyexe = (
            "python"
            if wilmaenv.venv is not None
            else "python{}.{}".format(*sys.version_info[:2])
        )

        args = [
            pyexe,
            "-m",
            "pip",
            "install",
            "--prefix",
            wilmaenv.wilmaprefix,
            "--no-input",
            "--no-python-version-warning",
        ]
        args += new_deps
        env = dict(os.environ)

        # Remove our custom sitecustomize from the env to avoid running pip
        # forever.
        if os.path.pathsep in env.get("PYTHONPATH", ""):
            _, _, pythonpath = env.get("PYTHONPATH", "").partition(os.path.pathsep)
            env["PYTHONPATH"] = pythonpath
        else:
            env["PYTHONPATH"] = ""
        check_output(args, env=env)

        metadata["dependencies"] = list(deps | installed_deps)

    if deps:
        sys.path.insert(0, *site.getsitepackages([wilmaenv.wilmaprefix]))

    # Import the requested modules
    imports = config.get("imports")

    # Install module watchdog
    try:
        ModuleWatchdog.install()
    except RuntimeError:
        pass
    atexit.register(ModuleWatchdog.uninstall)

    # Parse and apply probes
    probes = config.get("probes", {})
    if probes:
        LOGGER.info("Injecting statements ...")
        seen_locs = set()
        with cwd():
            for probe, statement in probes.items():
                loc, _, line = probe.rpartition(":")
                lineno = int(line)

                Probe(loc, lineno, statement, imports)

                if loc not in seen_locs:
                    seen_locs.add(loc)
                    try:
                        ModuleWatchdog.register_origin_hook(loc, on_import)
                    except ValueError:
                        print(
                            "wilma: source file '%s' not found. Skipping probe." % loc
                        )

    # Save metadata
    LOGGER.info("Writing metadata ...")
    wilmaenv.metadata_path.write_text(json.dumps(metadata))

except WilmaException:
    pass
