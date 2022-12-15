import typing as t
from pathlib import Path

import toml
from envier import En
from watchdog.events import FileModifiedEvent
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class WilmaFileChangeEvent(FileSystemEventHandler):
    def __init__(self, cb: t.Callable[[dict], None]) -> None:
        super().__init__()
        self.cb = cb

    def on_modified(self, event: FileModifiedEvent) -> None:
        super().on_modified(event)

        if Path(event.src_path).resolve() != wilmaenv.wilmafile.resolve():
            return

        new_config = toml.loads(wilmaenv.wilmafile.read_text())

        try:
            return self.cb(new_config)
        finally:
            wilmaenv.wilmaconfig = new_config


class WilmaConfig(En):
    wilmafile = En.v(
        Path,
        "wilmafile",
        default=Path("wilma.toml"),
    )

    wilmaprefix = En.v(
        Path,
        "wilmaprefix",
        default=Path(".wilma"),
    )

    venv = En.v(
        t.Optional[Path],
        "virtual_env",
        default=None,
    )

    verbose = En.v(
        bool,
        "wilmaverbose",
        default=False,
    )

    wilmaconfig = En.d(
        dict,
        lambda c: toml.loads(c.wilmafile.read_text()) if c.wilmafile.exists() else {},
    )
    metadata_path = En.d(Path, lambda c: c.wilmaprefix / "metadata.json")
    captures_path = En.d(Path, lambda c: c.wilmaprefix / "captures.log")

    observer = En.d(Observer, lambda _: Observer())

    def observe(self, cb):
        observer = self.observer
        observer.schedule(
            WilmaFileChangeEvent(cb), str(self.wilmafile.parent.resolve())
        )
        observer.start()


wilmaenv = WilmaConfig()
