__all__ = (
    "CLIContainer",
    "cli",
)

import typing as t
from contextlib import closing
from datetime import datetime
from pathlib import Path

import click
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
from asynchron.codegen.container import (
    CodeGeneratorContainer,
    CodeWriterContainer,
    ConfigReaderContainer,
    ConfigViewerContainer,
)
from asynchron.codegen.info import AsyncApiCodeGeneratorMetaInfo
from asynchron.codegen.spec.asyncapi import AsyncAPIObject, SpecObject
from asynchron.codegen.spec.transformer.null import NullTransformer
from asynchron.codegen.spec.transformer.walking import SpecObjectTitleNormalizer, SpecObjectWalkingTransformer
from asynchron.codegen.spec.viewer.settings import AsyncApiConfigViewSettings
from asynchron.codegen.spec.walker.spec_object_path import SpecObjectPath
from asynchron.providers import MappingValueSelector


def _load_config_source(path: Path, click_context: click.Context) -> t.TextIO:
    return click_context.with_resource(closing(path.open("r")))


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
    click_context: Provider[click.Context] = Dependency()
    config_path: Provider[Path] = Dependency()

    now: Provider[datetime] = Callable(datetime.utcnow)
    click_stdout: Provider[t.TextIO] = Singleton(
        click.get_text_stream,
        name="stdout",
    )

    config_source: Provider[t.TextIO] = Callable(
        _load_config_source,
        click_context=click_context.provided,
        path=config_path,
    )

    config_null_transformer: Provider[AsyncApiConfigTransformer] = Singleton(NullTransformer)
    config_titles_normalizer: Provider[AsyncApiConfigTransformer] = Singleton(
        SpecObjectWalkingTransformer,
        transformer=_normalize_spec_object_title,
    )

    config_readers: ConfigReaderContainer = Container(
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

    config_viewers: ConfigViewerContainer = Container(
        ConfigViewerContainer,
        output_stream=click_stdout,
    )
    code_generators: CodeGeneratorContainer = Container(
        CodeGeneratorContainer,
        now=now,
    )
    code_generator: MappingValueSelector[str, AsyncApiCodeGenerator] = MappingValueSelector({
        "python-aio-pika": code_generators.jinja_based_python_aio_pika,
    })
    generated_code: Provider[AsyncApiCodeGeneratorContent] = Callable(
        _generate_code_from_config,
        meta=code_generators.meta_info.provided,
        config=config,
        code_generator_factory=code_generator.provider,
    )

    code_writers: CodeWriterContainer = Container(
        CodeWriterContainer,
        output_stream=click_stdout,
    )
    code_writer: Provider[AsyncApiContentWriter] = Factory(
        code_writers.file_system,
    )

    action: Provider[object] = Callable(_raise_no_action_error)


@click.group("cli")
@click.option(
    "-f", "--file", "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=Path.cwd() / "asyncapi.yaml",
)
@click.pass_context
def cli(context: click.Context, config_path: Path) -> None:
    container = context.obj = (context.obj or CLIContainer(click_context=Object(context)))

    container.config_path.override(Object(config_path))


@cli.result_callback()
@click.pass_obj
def perform_cli_action(container: CLIContainer, *_: object, **__: object) -> None:
    container.action()


@cli.command("config")
@click.option("-q", "--quiet", is_flag=True, default=False)
@click.option("--indent", type=int, default=2)
@click.option("--pretty/--compact", is_flag=True, default=False)
@click.option("--show-null/--no-null", is_flag=True, default=False)
# FIXME: remove `sort_keys=True`, it is used for tests
@click.option("--sort-keys/--no-sort-keys", is_flag=True, default=True)
@click.option("--enable-normalize/--disable-normalize", is_flag=True, default=False)
@click.pass_obj
def config(
        container: CLIContainer,
        quiet: bool,
        pretty: bool,
        indent: int,
        show_null: bool,
        sort_keys: bool,
        enable_normalize: bool,
) -> None:
    if quiet:
        container.action.override(Callable(
            container.config_viewers.null.provided.view.call(),
            config=container.config,
        ))

    else:
        container.action.override(Callable(
            container.config_viewers.stream.provided.view.call(),
            config=container.config,
        ))
        container.config_viewers.stream.add_kwargs(
            settings=AsyncApiConfigViewSettings(
                show_null=show_null,
                prettified=pretty,
                indent=indent,
                sort_keys=sort_keys,
            ),
        )

    if not enable_normalize:
        container.config_titles_normalizer.override(container.config_null_transformer)


@cli.command("generate")
@click.argument("format", type=click.Choice(sorted(CLIContainer.code_generator.keys)))
@click.option("-o", "--output-dir", type=click.Path(exists=False, path_type=Path), default=Path.cwd(), )
@click.option("-p", "--project", type=str, default=None, )
@click.option("-d", "--dry-run", is_flag=True, default=False)
@click.option("--enable-main/--disable-main", is_flag=True, default=True)
# @click.option("--preview/--no-preview", is_flag=True, default=False)
@click.option("--enable-meta/--disable-meta", is_flag=True, default=True)
@click.option("--allow-formatter/--ignore-formatter", "ignore_formatter", is_flag=True, default=True)
@click.option("--use-absolute-imports/--use-relative-imports", is_flag=True, default=False)
@click.pass_obj
def generate(
        container: CLIContainer,
        format: str,
        output_dir: Path,
        project: t.Optional[str],
        dry_run: bool,
        enable_main: bool,
        enable_meta: bool,
        ignore_formatter: bool,
        use_absolute_imports: bool,
) -> None:
    container.generated_code.add_kwargs(
        code_generator_format=format,
    )

    container.code_generators.meta_info.add_kwargs(
        config_path=container.config_path,
        project_name=project if project is not None else output_dir.stem,
        enable_main=enable_main,
        enable_meta_doc=enable_meta,
        ignore_formatter=ignore_formatter,
        use_absolute_imports=use_absolute_imports,
    )

    container.action.override(Callable(
        container.code_writer.provided.write.call(),
        container.generated_code,
    ))

    if dry_run:
        container.code_writer.override(container.code_writers.stream)

    else:
        container.code_writer.add_kwargs(
            target_dir=output_dir,
        )


if __name__ == "__main__":
    cli()
