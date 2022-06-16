__all__ = (
    "AsyncApiNullContentWriter",
)

from asynchron.codegen.app import AsyncApiCodeGeneratorContent, AsyncApiContentWriter


class AsyncApiNullContentWriter(AsyncApiContentWriter):

    def write(self, content: AsyncApiCodeGeneratorContent) -> None:
        pass
