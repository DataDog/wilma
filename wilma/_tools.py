import contextlib
import ctypes
import inspect
import typing as t


@contextlib.contextmanager
def locals() -> t.Dict:
    """Context manager for mutating local variables."""
    frame = inspect.currentframe().f_back.f_back.f_back.f_back.f_back

    yield frame.f_locals

    # Commit the changes to the frame.
    ctypes.pythonapi.PyFrame_LocalsToFast(ctypes.py_object(frame), ctypes.c_int(1))
