__all__ = (
    "CodeWriterContainer",
)

import sys
import typing as t

from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Factory, Object, Provider, Singleton

from asynchron.codegen.app import AsyncApiContentWriter
from asynchron.codegen.writer.file_system import AsyncApiFileSystemContentWriter
from asynchron.codegen.writer.null import AsyncApiNullContentWriter
from asynchron.codegen.writer.stream import AsyncApiStreamContentWriter


class CodeWriterContainer(DeclarativeContainer):
    output_stream: Provider[t.TextIO] = Object(sys.stdout)

    null: Provider[AsyncApiContentWriter] = Singleton(
        AsyncApiNullContentWriter,
    )
    file_system: Provider[AsyncApiContentWriter] = Factory(
        AsyncApiFileSystemContentWriter,
    )
    stream: Provider[AsyncApiContentWriter] = Factory(
        AsyncApiStreamContentWriter,
        stream=output_stream,
    )
