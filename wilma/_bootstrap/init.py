# NOTE: This code gets run in the sitecustomize script
import atexit
import logging
import os
import site
import sys
from contextlib import contextmanager
from subprocess import check_output

from ddtrace.debugger._module import ModuleWatchdog
from wilma import _config
from wilma._inject import after_import

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
    # Load the configuration
    config_path = _config.get_path()
    if config_path is None:
        LOGGER.warn("No Wilma configuration file found.")
        raise WilmaException()

    config = _config.load(config_path)

    # Install dependencies in prefix
    deps = config.get("dependencies")
    if deps:
        prefix = os.path.abspath(os.getenv("_WILMAPREFIX") or ".wilma")
        pyexe = (
            "python"
            if os.getenv("VIRTUAL_ENV") is not None
            else "python{}.{}".format(*sys.version_info[:2])
        )

        args = [
            pyexe,
            "-m",
            "pip",
            "install",
            "--prefix",
            prefix,
            "--no-input",
            "--no-python-version-warning",
        ]
        args += [f"{p}{v.replace('latest', '')}" for p, v in deps.items()]
        env = dict(os.environ)

        # Remove our custom sitecustomize from the env to avoid running pip
        # forever.

        if os.path.pathsep in env.get("PYTHONPATH"):
            _, _, pythonpath = env.get("PYTHONPATH").partition(os.path.pathsep)
            env["PYTHONPATH"] = pythonpath
        else:
            env["PYTHONPATH"] = ""
        check_output(args, env=env)

        (sitepkg,) = site.getsitepackages([prefix])

        sys.path.insert(0, sitepkg)

    # Import the requested modules
    imports = config.get("imports")
    import_string = "\n".join(f"import {imp}" for imp in imports) if imports else ""

    # Install module watchdog
    ModuleWatchdog.install(on_run_module=True)
    atexit.register(ModuleWatchdog.uninstall)

    with cwd():
        # Parse and apply probes
        for probe, statement in config["probes"].items():
            loc, _, line = probe.rpartition(":")
            lineno = int(line)
            try:
                ModuleWatchdog.register_hook(
                    loc, after_import, (lineno, "\n".join((import_string, statement)))
                )
            except ValueError:
                print("wilma: source file '%s' not found. Skipping probe." % loc)

except WilmaException:
    pass
