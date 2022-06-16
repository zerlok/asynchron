__all__ = (
    "ConfigViewerContainer",
)

import sys
import typing as t

from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Object, Provider, Singleton

from asynchron.codegen.app import AsyncApiConfigViewer
from asynchron.codegen.spec.viewer.null import AsyncApiNullConfigViewer
from asynchron.codegen.spec.viewer.settings import AsyncApiConfigViewSettings
from asynchron.codegen.spec.viewer.stream import AsyncApiStreamConfigViewer


class ConfigViewerContainer(DeclarativeContainer):
    output_stream: Provider[t.TextIO] = Object(sys.stdout)

    settings: Provider[AsyncApiConfigViewSettings] = Singleton(AsyncApiConfigViewSettings)
    null: Provider[AsyncApiConfigViewer] = Singleton(
        AsyncApiNullConfigViewer,
    )
    stream: Provider[AsyncApiConfigViewer] = Singleton(
        AsyncApiStreamConfigViewer,
        stream=output_stream,
        settings=settings,
    )
