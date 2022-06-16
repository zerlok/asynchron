__all__ = (
    "AsyncApiFileSystemContentWriter",
)

from pathlib import Path

from asynchron.codegen.app import AsyncApiCodeGeneratorContent, AsyncApiContentWriter


class AsyncApiFileSystemContentWriter(AsyncApiContentWriter):

    def __init__(self, target_dir: Path) -> None:
        self.__target_dir = target_dir

    def write(self, content: AsyncApiCodeGeneratorContent) -> None:
        if not self.__target_dir.exists():
            self.__target_dir.mkdir(parents=True)

        for path, chunks in content:
            target = self.__target_dir.joinpath(path)

            with target.open("w") as fd:
                for chunk in chunks:
                    fd.write(chunk)
