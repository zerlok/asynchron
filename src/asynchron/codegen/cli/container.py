__all__ = (
    "CLIContainer",
)

import sys
import typing as t
from datetime import datetime
from pathlib import Path

from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import (
    Callable,
    Container,
    Dependency,
    Factory,
    List,
    Object,
    Provider,
    Singleton,
)

from asynchron.codegen.app import (
    AsyncApiCodeGenerator,
    AsyncApiCodeGeneratorContent,
    AsyncApiConfigReader,
    AsyncApiConfigTransformer,
    AsyncApiContentWriter,
)
from asynchron.codegen.generator.container import CodeGeneratorContainer
from asynchron.codegen.info import AsyncApiCodeGeneratorMetaInfo
from asynchron.codegen.spec.asyncapi import AsyncAPIObject, SpecObject
from asynchron.codegen.spec.reader.container import ConfigReaderContainer
from asynchron.codegen.spec.transformer.null import NullTransformer
from asynchron.codegen.spec.transformer.walking import SpecObjectTitleNormalizer, SpecObjectWalkingTransformer
from asynchron.codegen.spec.viewer.container import ConfigViewerContainer
from asynchron.codegen.spec.viewer.settings import AsyncApiConfigViewSettings
from asynchron.codegen.spec.walker.spec_object_path import SpecObjectPath
from asynchron.codegen.writer.container import CodeWriterContainer
from asynchron.providers import MappingValueSelector


def _load_config_from_source(
        normalized_config_reader_factory: t.Callable[[AsyncApiConfigReader], AsyncApiConfigReader],
        json_reference_resolved_config_reader_factory: t.Callable[[AsyncApiConfigReader, Path], AsyncApiConfigReader],
        format_specific_reader_factory: t.Callable[[str], AsyncApiConfigReader],
        source: t.TextIO,
        path: Path,
) -> AsyncAPIObject:
    reader = normalized_config_reader_factory(
        json_reference_resolved_config_reader_factory(
            format_specific_reader_factory(path.suffix[1:]),
            path,
        ),
    )

    return reader.read(source)


def _normalize_spec_object_title(path: SpecObjectPath, obj: SpecObject) -> SpecObject:
    return obj.accept_visitor(SpecObjectTitleNormalizer(path))


def _generate_code_from_config(
        code_generator_format: str,
        meta: AsyncApiCodeGeneratorMetaInfo,
        config: AsyncAPIObject,
        code_generator_factory: t.Callable[[str, AsyncApiCodeGeneratorMetaInfo], AsyncApiCodeGenerator],
) -> AsyncApiCodeGeneratorContent:
    return code_generator_factory(code_generator_format, meta).generate(config)


def _write_generated_code(
        writer: AsyncApiContentWriter,
        generator: AsyncApiCodeGenerator,
        config: AsyncAPIObject,
) -> None:
    return writer.write(generator.generate(config))


def _raise_no_action_error(*args: object, **kwargs: object) -> t.NoReturn:
    raise RuntimeError("CLI has no action for the specified command and arguments", args, kwargs)


class CLIContainer(DeclarativeContainer):
    config_path: Provider[Path] = Dependency()
    config_source_loader: Provider[t.Callable[[Path], t.TextIO]] = Dependency()

    stdout: Provider[t.TextIO] = Object(sys.stdout)
    now: Provider[datetime] = Callable(datetime.utcnow)

    config_source: Provider[t.TextIO] = Callable(
        # FIXME: Argument 1 to "Callable" has incompatible type "Provider[Callable[[Path], TextIO]]"; expected
        #  "Optional[Callable[..., TextIO]]"  [arg-type]
        config_source_loader,  # type: ignore
        config_path,
    )

    config_null_transformer: Provider[AsyncApiConfigTransformer] = Singleton(NullTransformer)
    config_titles_normalizer: Provider[AsyncApiConfigTransformer] = Singleton(
        SpecObjectWalkingTransformer,
        transformer=_normalize_spec_object_title,
    )

    config_readers: Container[ConfigReaderContainer] = Container(
        ConfigReaderContainer,
        transformers=List(config_titles_normalizer, ),
    )
    config: Provider[AsyncAPIObject] = Callable(
        _load_config_from_source,
        normalized_config_reader_factory=config_readers.normalized.provider,
        json_reference_resolved_config_reader_factory=config_readers.json_reference_resolved.provider,
        format_specific_reader_factory=config_readers.format_specific.provider,
        path=config_path,
        source=config_source,
    )

    config_view_settings: Factory[AsyncApiConfigViewSettings] = Factory(
        AsyncApiConfigViewSettings,
    )
    config_viewers: Container[ConfigViewerContainer] = Container(
        ConfigViewerContainer,
        output_stream=stdout,
        settings=config_view_settings,
    )
    code_generators: Container[CodeGeneratorContainer] = Container(
        CodeGeneratorContainer,
        now=now,
    )
    code_generator: MappingValueSelector[str, AsyncApiCodeGenerator] = MappingValueSelector({
        "python-aio-pika": code_generators.jinja_based_python_aio_pika,
    })
    generated_code: Callable[AsyncApiCodeGeneratorContent] = Callable(
        _generate_code_from_config,
        meta=code_generators.meta_info.provided,
        config=config,
        code_generator_factory=code_generator.provider,
    )

    code_writers: Container[CodeWriterContainer] = Container(
        CodeWriterContainer,
        output_stream=stdout,
    )
    code_writer: Factory[AsyncApiContentWriter] = Factory(
        code_writers.file_system,
    )

    action: Provider[object] = Callable(_raise_no_action_error)
