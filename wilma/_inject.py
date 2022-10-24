import inspect
import sys
import typing as t
from contextlib import contextmanager
from pathlib import Path
from types import FrameType
from types import ModuleType

from ddtrace.debugging._debugger import DebuggerModuleWatchdog
from ddtrace.debugging._function.discovery import FunctionDiscovery
from ddtrace.internal.injection import eject_hook
from ddtrace.internal.injection import inject_hook
from ddtrace.internal.module import origin

from wilma._deps import dependencies


@contextmanager
def cwd():
    sys.path.insert(0, Path.cwd())
    try:
        yield
    finally:
        sys.path.pop(0)


class Probe:
    __all__: t.Set["Probe"] = set()
    __injected__: t.Set["Probe"] = set()

    def __init__(
        self,
        filename: str,
        lineno: int,
        statement: str,
        imports: t.Optional[t.List[str]] = None,
    ) -> None:
        self.filename = str(Path(filename).resolve())
        self.lineno = lineno
        self.statement = statement
        self.imports = imports or []

        self._statement = "\n".join(
            ("\n".join(f"import {imp}" for imp in ("wilma", *self.imports)), statement)
        )

        self.__all__.add(self)

    def __hash__(self) -> int:
        return hash((self.filename, self.lineno, self._statement))

    def __repr__(self) -> str:
        return f"WilmaProbe({self.filename}:{self.lineno} -> {self.statement})"

    def __call__(self, frame: FrameType) -> None:
        return exec(self._statement, frame.f_globals, frame.f_locals)


def _wilma(probe: Probe) -> None:
    # If we get here, we are guaranteed a frame and its parent.
    frame = t.cast(FrameType, inspect.currentframe()).f_back
    try:
        probe(t.cast(FrameType, frame))
    except Exception:
        print(f"Error while executing {probe}")
        raise


def on_import(module: ModuleType) -> None:
    for probe in Probe.__all__:
        if probe in Probe.__injected__:
            continue

        if probe.filename == origin(module):
            # TODO: [perf] bulk inject probes
            for f in FunctionDiscovery.from_module(module).at_line(probe.lineno):
                try:
                    inject_hook(f, _wilma, probe.lineno, probe)
                    Probe.__injected__.add(probe)
                except Exception:
                    # TODO: Log failed injection
                    print("wilma: failed to inject probe %s" % probe)
                    pass


def on_config_changed(config) -> None:
    # Update dependencies
    dependencies.install(config)

    imports = config.get("imports")

    # Update probes
    Probe.__all__.clear()
    probes = config.get("probes", {})
    if probes:
        with cwd():
            for probe, statement in probes.items():
                loc, _, line = probe.rpartition(":")
                lineno = int(line)

                Probe(loc, lineno, statement, imports)

                try:
                    if "__main__" in sys.modules and origin(
                        sys.modules["__main__"]
                    ) == str(Path(loc).resolve()):
                        on_import(sys.modules["__main__"])
                    else:
                        DebuggerModuleWatchdog.register_origin_hook(loc, on_import)
                except ValueError:
                    print("wilma: source file '%s' not found. Skipping probe." % loc)

    for injected_probe in Probe.__injected__ - Probe.__all__:
        # These probes need to be removed
        module = DebuggerModuleWatchdog.get_by_origin(injected_probe.filename)
        if module is None:
            if (
                "__main__" in sys.modules
                and origin(sys.modules["__main__"]) == injected_probe.filename
            ):
                module = sys.modules["__main__"]
            if module is None:
                print("wilma: failed to find module for probe %s" % injected_probe)
                continue
        for f in FunctionDiscovery.from_module(module).at_line(injected_probe.lineno):
            try:
                eject_hook(f, _wilma, injected_probe.lineno, injected_probe)
                Probe.__injected__.remove(probe)
            except Exception:
                # TODO: Log failed ejection
                pass
