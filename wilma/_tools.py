import contextlib
import ctypes
import sys
import traceback
import typing as t
import weakref

from wilma._inject import Probe
from wilma._capture import CaptureContext


@contextlib.contextmanager
def locals() -> t.Dict:
    """Context manager for mutating local variables."""
    frame = sys._getframe().f_back.f_back.f_back.f_back.f_back

    yield frame.f_locals

    # Commit the changes to the frame.
    ctypes.pythonapi.PyFrame_LocalsToFast(ctypes.py_object(frame), ctypes.c_int(1))


def framestack(message: t.Optional[str] = None) -> None:
    """Print the current frame stack.

    An optional argument to print at the end can also be passed to this helper.
    """
    frame = sys._getframe()
    probe_frame = frame.f_back.f_back
    caller_frame = probe_frame.f_back.f_back

    probe: Probe = probe_frame.f_locals["self"]

    print(
        f"Frame stack from {probe.filename}, line {probe.lineno}, in {caller_frame.f_code.co_name} (top-most frame last):"
    )

    traceback.print_stack(caller_frame.f_back, file=sys.stdout)

    if message is not None:
        print(message)


_watches = {}
_captureOutputs: t.List[t.Callable] = []

def _register_capture_output(callback: t.Callable):
    _captureOutputs.append(callback)


def watch(name: str, value: t.Any):
    _watches[name] = value
    weakref.finalize(value, lambda name: _watches.pop(name,None) , name)


def capture():
    frame = sys._getframe(4) #get caller frame
    context = CaptureContext(frame)
    for name,w in _watches:
        context.add_watch(name, w)
    context.capture()
    capture = context.to_json()
    for output in _captureOutputs:
        output(capture)
