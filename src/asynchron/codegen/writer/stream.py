__all__ = (
    "AsyncApiStreamContentWriter",
)

import typing as t
from pathlib import Path

from asynchron.codegen.app import AsyncApiContentWriter


class AsyncApiStreamContentWriter(AsyncApiContentWriter):

    def __init__(self, stream: t.TextIO) -> None:
        self.__stream = stream

    def write(self, content: t.Iterable[t.Tuple[Path, t.Iterable[str]]]) -> None:
        for path, chunks in content:
            self.__stream.write(f"# {'-' * 30}\n")
            self.__stream.write(f"# {path}\n")
            self.__stream.write(f"# {'-' * 30}\n")

            for chunk in chunks:
                self.__stream.write(chunk)

            self.__stream.write("\n")
