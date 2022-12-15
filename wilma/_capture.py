from itertools import chain, islice
import os
import sys
import threading
from types import FrameType
from typing import (Any, Dict, Type)
from ddtrace.debugging._encoding import (_get_fields, _qualname)
from ddtrace.internal.compat import BUILTIN_CONTAINER_TYPES
from ddtrace.internal.compat import BUILTIN_SIMPLE_TYPES
from ddtrace.internal.safety import get_slots
from ddtrace.internal.utils.cache import cached

NoneType = type(None)
GetSetDescriptor = type(type.__dict__["__dict__"])  # type: ignore[index]

MAXLEVEL = 10
MAXSIZE = 100
MAXLEN = 255
MAXFIELDS = 20
MAXOBJECTS = 500

class CaptureContext:
    def __init__(self, frame: FrameType=None, level=MAXLEVEL, maxlen=MAXLEN, maxsize=MAXSIZE, maxfields=MAXFIELDS, maxobjects=MAXOBJECTS):
        self.frame = frame or sys._getframe(1)
        self.maxlevel = level
        self.maxlen = maxlen
        self.maxsize = maxsize
        self.maxfields = maxfields
        self.maxobjects = maxobjects

        self._locals = {name: id(item) for (name,item) in frame.f_locals.items()}
        self._watches = {}

        self.to_capture = [(item, level) for item in frame.f_locals.values()]

        self.captured = {}
        self.capturedSize = 0

    def add_watch(self, name, object):
        self._watches[name] = id(object);
        self.to_capture.append((object, 0))


    def capture_value(self, _id ,value, level:int):
        _type = type(value)

        if _type in BUILTIN_SIMPLE_TYPES:
            if _type is NoneType:
                return ({"id": _id, "type": "NoneType", "isNull": True}, [])

            value_repr = repr(value)
            value_repr_len = len(value_repr)
            val = (
                {
                    "id": _id, 
                    "type": _qualname(_type),
                    "value": value_repr,
                }
                if value_repr_len <= self.maxlen
                else {
                    "id": _id, 
                    "type": _qualname(_type),
                    "value": value_repr[:self.maxlen],
                    "truncated": True,
                    "size": value_repr_len,
                }
            )

            return (val, [])
        if _type in BUILTIN_CONTAINER_TYPES:
            if level < 0:
                return ({
                    "id": _id, 
                    "type": _qualname(_type),
                    "notCapturedReason": "depth",
                    "size": len(value),
                }, [])

            if _type is dict:
                items = list(islice(value.items(),self.maxsize))
                # Mapping
                data = {
                    "id": _id, 
                    "type": "dict",
                    "entries": [
                        (
                            id(item[0]),
                            id(item[1]),
                        )
                        for item in items
                    ],
                    "size": len(value),
                }
                if level > 0:
                    to_capture = chain(
                        [(item[0],level - 1) for item in items],
                        [(item[1],level - 1) for item in items],
                    )
                else:
                    to_capture = []

            else:
                # Sequence
                data = {
                    "id": _id, 
                    "type": _qualname(_type),
                    "elements": [id(v) for v in value[:self.maxsize]],
                    "size": len(value),
                }
                if level > 0:
                    to_capture = [(v,level - 1) for v in value[:self.maxsize]]
                else:
                    to_capture = []

            if len(value) > self.maxsize:
                data["notCapturedReason"] = "collectionSize"

            return (data, to_capture)

        fields = _get_fields(value)
        data = {
            "id": _id,
            "type": _qualname(_type),
            "fields": {
                n:id(v) for _, (n, v) in zip(range(self.maxfields), fields.items())
            },
        }

        to_capture = [(v, level - 1) for v in zip(range(self.maxfields), fields.values())]

        if len(fields) > self.maxfields:
            data["notCapturedReason"] = "fieldCount"

        return (data, to_capture)

    def capture(self):
        while self.capturedSize < self.maxobjects and len(self.to_capture) > 0:
            (obj,level) = self.to_capture.pop()
            _id = id(obj)
            (captured, to_capture) = self.capture_value(_id, obj, level)

            self.captured[_id] = captured
            for obj_and_level in to_capture:
                to_capture_id = id(obj_and_level[0])
                if to_capture_id not in self.captured:
                    self.to_capture.append(obj_and_level)

            self.capturedSize += 1
        
        # remove all left overs
        self.to_capture.clear()

    def capture_stack(self):
        frame = self.frame
        stack = []
        h = 0
        while frame and h < self.maxsize:
            code = frame.f_code
            stack.append(
                {
                    "fileName": code.co_filename,
                    "function": code.co_name,
                    "lineNumber": frame.f_lineno,
                }
            )
            frame = frame.f_back
            h += 1
        return stack

    def capture_thread(self):
        thread = threading.current_thread()
        return dict(
            fid = id(self.frame), 
            tid= thread.ident,
            pid= os.getpid()
        )

    def to_json(self):
        return dict(
            type = "snapshot",
            locals = self._locals,
            watches = self._watches,
            objects = list(self.captured.values()),
            stack = self.capture_stack(),
            **self.capture_thread()
        )

def capture(frame: FrameType = None):
    context = CaptureContext(frame or sys._getframe(1))
    context.capture()
    return context.to_json()
