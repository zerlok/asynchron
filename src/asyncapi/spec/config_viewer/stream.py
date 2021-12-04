__all__ = (
    "AsyncApiStreamConfigViewer",
)

import typing as t

from asyncapi.app import AsyncApiConfigViewer
from asyncapi.spec.base import AsyncAPIObject
from asyncapi.spec.config_viewer.settings import AsyncApiConfigViewSettings


class AsyncApiStreamConfigViewer(AsyncApiConfigViewer):

    def __init__(self, stream: t.TextIO, settings: AsyncApiConfigViewSettings) -> None:
        self.__stream = stream
        self.__settings = settings

    def view(self, config: AsyncAPIObject) -> None:
        content = config.json(
            by_alias=True,
            exclude_none=not self.__settings.show_null,
            indent=self.__settings.indent if self.__settings.prettified else None,
            separators=(", ", ": ") if self.__settings.prettified else (",", ":"),
            sort_keys=self.__settings.sort_keys,
        )

        self.__stream.write(f"{content}\n")
