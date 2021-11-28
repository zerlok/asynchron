__all__ = (
    "AsyncApiStreamCodeWriter",
)

import typing as t
from pathlib import Path

from asyncapi.app import AsyncApiCodeWriter


class AsyncApiStreamCodeWriter(AsyncApiCodeWriter):

    def __init__(self, stream: t.TextIO) -> None:
        self.__stream = stream

    def write(self, path: Path, content: t.Iterable[str]) -> None:
        self.__stream.write(f"# {'-' * 30}\n")
        self.__stream.write(f"# {path}\n")
        self.__stream.write(f"# {'-' * 30}\n")

        for chunk in content:
            self.__stream.write(chunk)

        self.__stream.write("\n")
