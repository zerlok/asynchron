__all__ = (
    "AsyncApiNullConfigViewer",
)

from asynchron.codegen.app import AsyncApiConfigViewer
from asynchron.codegen.spec.asyncapi import AsyncAPIObject


class AsyncApiNullConfigViewer(AsyncApiConfigViewer):

    def view(self, config: AsyncAPIObject) -> None:
        pass
