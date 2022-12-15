import json
import logging
import os
import site
import sys
from subprocess import check_output

from wilma._config import wilmaenv


LOGGER = logging.getLogger(__name__)


class Dependencies:
    __all__ = set()
    __installed__ = set()

    def __init__(self) -> None:
        self._path_updated = False
        self.metadata = (
            json.loads(wilmaenv.metadata_path.read_text())
            if wilmaenv.metadata_path.exists()
            else {}
        )

        self.__installed__.update(self.metadata.get("dependencies", []))

    def install(self, config):
        deps = {
            f"{p}{v.replace('latest', '')}"
            for p, v in config.get("dependencies", {}).items()
        }

        new_deps = list(deps - self.__installed__)

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

            self.__installed__.update(deps)

            self.metadata["dependencies"] = list(self.__installed__)

        # TODO: Uninstall dependencies that are no longer needed

        if not self._path_updated and deps:
            sys.path.insert(0, *site.getsitepackages([wilmaenv.wilmaprefix]))
            self._path_updated = True

        wilmaenv.metadata_path.write_text(json.dumps(self.metadata))


dependencies = Dependencies()
