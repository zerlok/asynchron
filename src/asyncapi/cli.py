__all__ = (
    "cli",
)

import typing as t
from contextlib import closing
from pathlib import Path

import click
from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Callable, Object, Provider, Singleton

from asyncapi.app import (
    AsyncApiCodeGenerator,
    AsyncApiCodeWriter, AsyncApiConfigReader,
)
from asyncapi.providers import MappingValueSelector
from asyncapi.spec.code_generator.jinja.python_aio_pika import JinjaBasedPythonAioPikaCodeGenerator
from asyncapi.spec.code_writer.file_system import AsyncApiFileSystemCodeWriter
from asyncapi.spec.code_writer.stream import AsyncApiStreamCodeWriter
from asyncapi.spec.config_reader.json import JsonAsyncApiConfigReader
from asyncapi.spec.config_reader.transformer import AsyncApiConfigTransformingConfigReader
from asyncapi.spec.config_reader.yaml import YamlAsyncApiConfigReader
from asyncapi.spec.transformer.reference_resolver import ReferenceResolvingAsyncAPIObjectTransformer


class CLIContainer(DeclarativeContainer):
    config_path = Provider[Path]()
    config_source = Provider[t.TextIO]()
    config_transformers = Singleton(
        lambda: (ReferenceResolvingAsyncAPIObjectTransformer(),),
    )

    config_reader: MappingValueSelector[str, AsyncApiConfigReader] = MappingValueSelector(
        {
            ".yml": Singleton(YamlAsyncApiConfigReader),
            ".yaml": Singleton(YamlAsyncApiConfigReader),
            ".json": Singleton(JsonAsyncApiConfigReader),
        },
        config_path.provided.suffix,
    )
    normalized_config_reader = Singleton(
        AsyncApiConfigTransformingConfigReader,
        reader=config_reader,
        transformers=config_transformers,
    )
    config = Singleton(
        normalized_config_reader.provided.read.call(),
        source=config_source,
    )

    code_generator_format = Provider[str]()
    code_generator: MappingValueSelector[str, AsyncApiCodeGenerator] = MappingValueSelector(
        {
            "python-aio-pika": Singleton(JinjaBasedPythonAioPikaCodeGenerator),
        },
        code_generator_format.provided,
    )
    code_generator_dry_run = Provider[bool]()
    code_generator_target_dir = Provider[Path]()
    code_generator_output_stream = Provider[t.TextIO]()
    code_writer: MappingValueSelector[bool, AsyncApiCodeWriter] = MappingValueSelector(
        {
            False: Singleton(AsyncApiFileSystemCodeWriter, target_dir=code_generator_target_dir),
            True: Singleton(AsyncApiStreamCodeWriter, stream=code_generator_output_stream),
        },
        code_generator_dry_run.provided,
    )


@click.group("cli")
@click.option(
    "-f", "--file",
    type=click.Path(exists=True, path_type=Path),
    default=Path.cwd() / "asyncapi.yaml",
)
@click.pass_context
def cli(context: click.Context, file: Path) -> None:
    container = context.obj = CLIContainer()

    container.code_generator_output_stream.override(Object(click.get_text_stream("stdout")))

    container.config_path.override(Object(file))
    container.config_source.override(Callable(lambda: context.with_resource(closing(file.open("r")))))


@cli.command("get")
@click.option("--pretty/--compact", is_flag=True, default=False)
@click.option("--show-null/--no-null", default=False)
@click.pass_obj
def get_config(container: CLIContainer, pretty: bool, show_null: bool) -> None:
    config = container.config()
    # FIXME: remove `sort_keys=True`, it is used for tests
    click.echo(config.json(by_alias=True, exclude_none=not show_null, indent=2 if pretty else None,
                           separators=(", ", ": ") if pretty else (",", ":"), sort_keys=True))


@cli.command("generate")
@click.argument("format", type=click.Choice(sorted(CLIContainer.code_generator.keys)))
@click.option("-o", "--output-dir", type=click.Path(exists=False, path_type=Path), default=Path.cwd(), )
@click.option("-d", "--dry-run", is_flag=True, default=False)
@click.pass_obj
def generate_code(container: CLIContainer, format: str, output_dir: Path, dry_run: bool) -> None:
    container.code_generator_format.override(Object(format))
    container.code_generator_target_dir.override(Object(output_dir))
    container.code_generator_dry_run.override(Object(dry_run))

    config = container.config()
    code_generator = container.code_generator()
    code_writer = container.code_writer()

    for destination_path, content in code_generator.generate(config):
        code_writer.write(destination_path, content)


if __name__ == "__main__":
    cli()
