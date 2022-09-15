import inspect
import typing as t
from pathlib import Path
from types import FrameType
from types import ModuleType

from ddtrace.debugging._function.discovery import FunctionDiscovery
from ddtrace.internal.injection import inject_hook
from ddtrace.internal.module import origin


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
            ("\n".join(f"import {imp}" for imp in self.imports), statement)
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
        if probe.filename == origin(module):
            # TODO: [perf] bulk inject probes
            for f in FunctionDiscovery(module).at_line(probe.lineno):
                inject_hook(f, _wilma, probe.lineno, probe)
