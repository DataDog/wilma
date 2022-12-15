import contextlib
import ctypes
import sys
import traceback
import typing as t

from wilma._inject import Probe


@contextlib.contextmanager
def locals() -> t.Generator[t.Dict[str, t.Any], None, None]:
    """Context manager for mutating local variables."""
    frame = sys._getframe(5)

    yield frame.f_locals

    # Commit the changes to the frame.
    ctypes.pythonapi.PyFrame_LocalsToFast(ctypes.py_object(frame), ctypes.c_int(1))


def framestack(message: t.Optional[str] = None) -> None:
    """Print the current frame stack.

    An optional argument to print at the end can also be passed to this helper.
    """
    probe_frame = sys._getframe(2)
    caller_frame = sys._getframe(4)

    probe: Probe = probe_frame.f_locals["self"]

    print(
        f"Frame stack from {probe.filename}, line {probe.lineno}, in {caller_frame.f_code.co_name} (top-most frame last):"
    )

    traceback.print_stack(caller_frame.f_back, file=sys.stdout)

    if message is not None:
        print(message)
