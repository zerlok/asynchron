__all__ = (
    "CLIContainer",
    "cli",
)

import typing as t
from contextlib import closing
from datetime import datetime
from getpass import getuser
from pathlib import Path

import click
from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Callable, Object, Provider, Singleton

from asynchron.codegen.app import (
    AsyncApiCodeGenerator,
    AsyncApiConfigReader,
    AsyncApiConfigTransformer,
    AsyncApiContentWriter,
)
from asynchron.codegen.generator.jinja.python_aio_pika import JinjaBasedPythonAioPikaCodeGenerator
from asynchron.codegen.info import AsyncApiCodeGeneratorMetaInfo
from asynchron.codegen.spec.base import AsyncAPIObject, SpecObject
from asynchron.codegen.spec.reader.json import JsonAsyncApiConfigReader
from asynchron.codegen.spec.reader.transformer import AsyncApiConfigTransformingConfigReader
from asynchron.codegen.spec.reader.yaml import YamlAsyncApiConfigReader
from asynchron.codegen.spec.transformer.json_reference_resolver import JsonReferenceResolvingTransformer
from asynchron.codegen.spec.transformer.schema_object_title_normalizer import (
    SpecObjectTitleNormalizer,
    SpecObjectTransformer,
)
from asynchron.codegen.spec.viewer.settings import AsyncApiConfigViewSettings
from asynchron.codegen.spec.viewer.stream import AsyncApiStreamConfigViewer
from asynchron.codegen.spec.walker.spec_object_path import SpecObjectPath
from asynchron.codegen.writer.file_system import AsyncApiFileSystemContentWriter
from asynchron.codegen.writer.stream import AsyncApiStreamContentWriter
from asynchron.providers import MappingValueSelector


@SpecObjectTransformer
def normalize_spec_object_title(path: SpecObjectPath, obj: SpecObject) -> SpecObject:
    return obj.accept_visitor(SpecObjectTitleNormalizer(path))


def _load_config_source(path: Path, click_context: click.Context) -> t.TextIO:
    return click_context.with_resource(closing(path.open("r")))


def _create_config_normalizers(
        *normalizers: AsyncApiConfigTransformer,
) -> t.Sequence[AsyncApiConfigTransformer]:
    return (
        *normalizers,
        JsonReferenceResolvingTransformer(),
    )


def _write_generated_code(
        writer: AsyncApiContentWriter,
        generator: AsyncApiCodeGenerator,
        config: AsyncAPIObject,
) -> None:
    return writer.write(generator.generate(config))


class CLIContainer(DeclarativeContainer):
    now = Callable(datetime.utcnow)
    stdout = Singleton(
        click.get_text_stream,
        name="stdout",
    )

    click_context = Callable(click.Context, command=click.Command(None))
    config_path = Provider[Path]()
    code_generator_format = Provider[str]()
    config_viewer_settings = Provider[AsyncApiConfigViewSettings]()

    load_config_source = Callable(
        _load_config_source,
        path=config_path.provided,
        click_context=click_context.provided,
    )
    config_transformers = Singleton(
        _create_config_normalizers,
    )
    config_reader_impl: MappingValueSelector[str, AsyncApiConfigReader] = MappingValueSelector(
        {
            ".yml": Singleton(YamlAsyncApiConfigReader),
            ".yaml": Singleton(YamlAsyncApiConfigReader),
            ".json": Singleton(JsonAsyncApiConfigReader),
        },
        key=config_path.provided.suffix,
    )
    normalized_config_reader = Singleton(
        AsyncApiConfigTransformingConfigReader,
        reader=config_reader_impl.provided,
        transformers=config_transformers.provided,
    )
    config = Singleton(
        normalized_config_reader.provided.read.call(),
        source=load_config_source.provided,
    )

    config_viewer_impl = Singleton(
        AsyncApiStreamConfigViewer,
        stream=stdout.provided,
        settings=config_viewer_settings.provided,
    )

    # code_generator_project_name = Provider[str]()
    # code_generator_project_author = Callable(getuser)
    code_generator_meta_info = Provider[AsyncApiCodeGeneratorMetaInfo]()
    code_generator_impl: MappingValueSelector[str, AsyncApiCodeGenerator] = MappingValueSelector(
        {
            "python-aio-pika": Singleton(
                JinjaBasedPythonAioPikaCodeGenerator,
                code_generator_meta_info.provided,
            ),
        },
        key=code_generator_format.provided,
    )

    code_writer_target_dir = Provider[Path]()
    code_writer_dry_run = Provider[bool]()
    code_writer_impl: MappingValueSelector[bool, AsyncApiContentWriter] = MappingValueSelector(
        {
            False: Singleton(AsyncApiFileSystemContentWriter, target_dir=code_writer_target_dir),
            True: Singleton(AsyncApiStreamContentWriter, stream=stdout),
        },
        key=code_writer_dry_run.provided,
    )

    view_read_config = Callable(
        config_viewer_impl.provided.view.call(),
        config=config.provided,
    )
    write_generated_code = Callable(
        _write_generated_code,
        writer=code_writer_impl.provided,
        generator=code_generator_impl.provided,
        config=config.provided,
    )


@click.group("cli")
@click.option(
    "-f", "--file",
    type=click.Path(exists=True, path_type=Path),
    default=Path.cwd() / "asyncapi.yaml",
)
@click.pass_context
def cli(context: click.Context, file: Path) -> None:
    container = context.obj = (context.obj or CLIContainer())

    container.click_context.override(Object(context))
    container.config_path.override(Object(file))


@cli.command("get")
@click.option("--pretty/--compact", is_flag=True, default=False)
@click.option("--show-null/--no-null", default=False)
@click.pass_obj
def get_config(container: CLIContainer, pretty: bool, show_null: bool) -> None:
    container.config_viewer_settings.override(Object(AsyncApiConfigViewSettings(
        show_null=show_null,
        prettified=pretty,
        indent=2,
        # FIXME: remove `sort_keys=True`, it is used for tests
        sort_keys=True,
    )))

    container.view_read_config()


@cli.command("generate")
@click.argument("format", type=click.Choice(sorted(CLIContainer.code_generator_impl.keys)))
@click.option("-p", "--project", type=str, default=Path.cwd().stem, )
@click.option("-o", "--output-dir", type=click.Path(exists=False, path_type=Path), default=Path.cwd(), )
@click.option("-d", "--dry-run", is_flag=True, default=False)
@click.option("--enable-meta/--disable-meta", is_flag=True, default=True)
@click.option("--allow-formatter/--ignore-formatter", is_flag=True, default=False)
@click.option("--use-absolute-imports/--use-relative-imports", is_flag=True, default=True)
@click.pass_obj
def generate_code(
        container: CLIContainer,
        format: str,
        project: str,
        output_dir: Path,
        dry_run: bool,
        enable_meta: bool,
        allow_formatter: bool,
        use_absolute_imports: bool,
) -> None:
    container.config_transformers.add_args(normalize_spec_object_title)
    container.code_generator_meta_info.override(Object(AsyncApiCodeGeneratorMetaInfo(
        generator_name="asynchron",
        generator_link="https://github.com/zerlok/asynchron",
        generator_started_at=container.now(),
        config_path=container.config_path(),
        project_name=project,
        author=getuser(),
        enable_meta_doc=enable_meta,
        ignore_formatter=not allow_formatter,
        use_absolute_imports=use_absolute_imports,
    )))
    container.code_generator_format.override(Object(format))
    container.code_writer_target_dir.override(Object(output_dir))
    container.code_writer_dry_run.override(Object(dry_run))

    container.write_generated_code()


if __name__ == "__main__":
    cli()
