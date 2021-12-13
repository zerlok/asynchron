__all__ = (
    "AsyncApiFileSystemContentWriter",
)

import typing as t
from pathlib import Path

from asynchron.codegen.app import AsyncApiContentWriter


class AsyncApiFileSystemContentWriter(AsyncApiContentWriter):

    def __init__(self, target_dir: Path) -> None:
        self.__target_dir = target_dir

    def write(self, content: t.Iterable[t.Tuple[Path, t.Iterable[str]]]) -> None:
        if not self.__target_dir.exists():
            self.__target_dir.mkdir(parents=True)

        for path, chunks in content:
            target = self.__target_dir.joinpath(path)

            with target.open("w") as fd:
                for chunk in chunks:
                    fd.write(chunk)
