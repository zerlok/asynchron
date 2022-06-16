import sys
import typing as t
from datetime import datetime
from getpass import getuser
from pathlib import Path

from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Callable, Factory, List, Object, Provider, Singleton

from asynchron.codegen.app import (
    AsyncApiCodeGenerator,
    AsyncApiConfigReader,
    AsyncApiConfigTransformer,
    AsyncApiConfigViewer,
    AsyncApiContentWriter,
)
from asynchron.codegen.generator.jinja.jinja_renderer import JinjaTemplateRenderer
from asynchron.codegen.generator.jinja.python_aio_pika import JinjaBasedPythonAioPikaCodeGenerator
from asynchron.codegen.generator.json_schema_python_def import (
    JsonSchemaBasedPythonPrimitiveDefGenerator,
    JsonSchemaBasedPythonStructuredDataModelDefGenerator,
    JsonSchemaBasedTypeDefGenerator,
)
from asynchron.codegen.info import AsyncApiCodeGeneratorMetaInfo
from asynchron.codegen.spec.reader.json import JsonAsyncApiConfigReader
from asynchron.codegen.spec.reader.transformer import AsyncApiConfigTransformingConfigReader
from asynchron.codegen.spec.reader.yaml import YamlAsyncApiConfigReader
from asynchron.codegen.spec.transformer.json_reference_resolver import JsonReferenceResolvingTransformer
from asynchron.codegen.spec.viewer.null import AsyncApiNullConfigViewer
from asynchron.codegen.spec.viewer.stream import AsyncApiStreamConfigViewer
from asynchron.codegen.writer.file_system import AsyncApiFileSystemContentWriter
from asynchron.codegen.writer.null import AsyncApiNullContentWriter
from asynchron.codegen.writer.stream import AsyncApiStreamContentWriter
from asynchron.providers import MappingValueSelector


def _create_json_reference_resolving_config_reader(
        reader: AsyncApiConfigReader,
        path: Path,
        json_resolving_transformer_factory: t.Callable[[Path], AsyncApiConfigTransformer],
) -> AsyncApiConfigReader:
    return AsyncApiConfigTransformingConfigReader(reader, [json_resolving_transformer_factory(path), ])


class ConfigReaderContainer(DeclarativeContainer):
    yaml: Provider[AsyncApiConfigReader] = Singleton(YamlAsyncApiConfigReader)
    json: Provider[AsyncApiConfigReader] = Singleton(JsonAsyncApiConfigReader)

    format_specific: Provider[AsyncApiConfigReader] = MappingValueSelector({
        "yml": yaml,
        "yaml": yaml,
        "json": json,
    })

    json_reference_resolving_config_transformer: Provider[JsonReferenceResolvingTransformer] = Factory(
        JsonReferenceResolvingTransformer,
    )
    json_reference_resolved: Provider[AsyncApiConfigReader] = Callable(
        _create_json_reference_resolving_config_reader,
        json_resolving_transformer_factory=json_reference_resolving_config_transformer.provider,
    )

    transformers: Provider[t.Sequence[AsyncApiConfigTransformer]] = List()
    normalized: Provider[AsyncApiConfigReader] = Factory(
        AsyncApiConfigTransformingConfigReader,
        transformers=transformers,
    )


class ConfigViewerContainer(DeclarativeContainer):
    output_stream: Provider[t.TextIO] = Object(sys.stdout)
    null: Provider[AsyncApiConfigViewer] = Singleton(
        AsyncApiNullConfigViewer,
    )
    stream: Provider[AsyncApiConfigViewer] = Singleton(
        AsyncApiStreamConfigViewer,
        stream=output_stream,
    )


class CodeGeneratorContainer(DeclarativeContainer):
    now: Provider[datetime] = Callable(datetime.utcnow)

    meta_info: Provider[AsyncApiCodeGeneratorMetaInfo] = Factory(
        AsyncApiCodeGeneratorMetaInfo,
        generator_name=Object("asynchron"),
        generator_link=Object("https://github.com/zerlok/asynchron"),
        generator_started_at=now,
        author=Callable(getuser),
    )

    python_primitive_def_generator: Provider[JsonSchemaBasedTypeDefGenerator] = Singleton(
        JsonSchemaBasedPythonPrimitiveDefGenerator,
    )
    python_complex_def_generator: Provider[JsonSchemaBasedTypeDefGenerator] = Singleton(
        JsonSchemaBasedPythonStructuredDataModelDefGenerator,
        python_primitive_def_generator,
    )

    jinja_template_renderer: Provider[t.Optional[JinjaTemplateRenderer]] = Object(
        None,
    )
    jinja_based_python_aio_pika: Provider[AsyncApiCodeGenerator] = Factory(
        JinjaBasedPythonAioPikaCodeGenerator,
        message_def_generator=python_complex_def_generator,
        renderer=jinja_template_renderer,
    )


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
