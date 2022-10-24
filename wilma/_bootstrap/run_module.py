import runpy
import typing as t
from traceback import print_tb
from types import CodeType

from bytecode import Bytecode
from bytecode import Instr
from ddtrace.internal.injection import _inject_hook
from ddtrace.internal.utils import get_argument_value

from wilma._inject import Probe
from wilma._inject import _wilma


def instrs(code: Bytecode) -> t.Iterator[Instr]:
    return (_ for _ in code if isinstance(_, Instr))


def transform_code(code: CodeType, module_origin: str) -> CodeType:
    # Transform a module code object recursively. We know that everything in a
    # module is defined by executing the bytecode from a code object, so we can
    # conveniently look at instruction arguments to build a tree of code objects
    # that we can recursevely iterate upon.
    acode = Bytecode.from_code(code)

    # Select the probes that apply to the run module.
    # TODO: Add indexing to optimise this lookup.
    probes = [p for p in Probe.__all__ if p.filename == module_origin]
    if not probes:
        # We don't have probes for the run module, so we return the original
        # code object.
        return code

    linenos = {instr.lineno for instr in instrs(acode)}
    for probe in probes:
        # TODO: Add indexing to optimise this lookup.
        if probe.lineno not in linenos:
            continue

        # We inject the hook only if the probe is on a line that belongs to this
        # code object.
        _inject_hook(acode, _wilma, probe.lineno, probe)
        Probe.__injected__.add(probe)

    # Scan all the instructions to find any code objects in the arguments that
    # we should recurse upon to make sure that we look at the whole run module.
    for i in instrs(acode):
        if isinstance(i.arg, CodeType):
            i.arg = transform_code(i.arg, module_origin)

    # Return the new code object.
    return acode.to_code()


def _wrapped_run_code(*args, **kwargs):
    # type: (*t.Any, **t.Any) -> t.Dict[str, t.Any]
    global _run_code, _post_run_module_hooks

    code = args[0] if args else kwargs.pop("code")
    try:
        mod_spec = get_argument_value(args, kwargs, 4, "mod_spec")
    except Exception:
        mod_spec = None
    try:
        script_name = get_argument_value(args, kwargs, 6, "script_name")
    except Exception:
        script_name = None

    try:
        fname = script_name if mod_spec is None else mod_spec.origin
        new_code = code if fname is None else transform_code(code, fname)
    except Exception as e:
        print("Error in pre_run_module hook. Traceback:")
        print_tb(e.__traceback__)
        print(f"{type(e).__name__}: {e}")
        new_code = code

    return _run_code(new_code, *args[1:], **kwargs)


_run_code = runpy._run_code  # type: ignore[attr-defined]
runpy._run_code = _wrapped_run_code  # type: ignore[attr-defined]
