__all__ = (
    "AsyncApiFileSystemCodeWriter",
)

import typing as t
from pathlib import Path

from asyncapi.app import AsyncApiCodeWriter


class AsyncApiFileSystemCodeWriter(AsyncApiCodeWriter):

    def __init__(self, target_dir: Path) -> None:
        self.__target_dir = target_dir

    def write(self, path: Path, content: t.Iterable[str]) -> None:
        target = self.__target_dir.joinpath(path)

        with target.open("w") as fd:
            for chunk in content:
                fd.write(chunk)
