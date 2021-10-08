import inspect

from ddtrace.debugger._function.map import FunctionLineMap
from ddtrace.debugger._function.store import FunctionStore

_STORE = FunctionStore()
_INJECTED = set()


def _wilma(statement):
    frame = inspect.currentframe().f_back
    exec(statement, frame.f_globals, frame.f_locals)


def after_import(module, arg):
    lineno, statement = arg
    if arg in _INJECTED:
        return

    for f in FunctionLineMap(module).get_functions_at_line(lineno):
        _STORE.inject_hook(f, _wilma, lineno, statement)
        _INJECTED.add(arg)
