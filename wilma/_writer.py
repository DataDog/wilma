import json
import typing as t
from pathlib import Path


class JsonFileWriter(object):
    def __init__(self, path: Path):
        self.path = path
        self.stream: t.Optional[t.TextIO] = None

    def write(self, capture):
        if self.stream is None:
            self.stream = self.path.open("a")

        print(json.dumps(capture), file=self.stream)

    def __del__(self):
        if self.stream is not None:
            self.stream.close()
