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
    AsyncApiConfigReader,
    read_config,
)
from asyncapi.providers import KeySelector
from asyncapi.spec.code_generator.jinja.python_aio_pika import JinjaBasedPythonAioPikaCodeGenerator
from asyncapi.spec.config_reader.json import JsonAsyncApiConfigReader
from asyncapi.spec.config_reader.yaml import YamlAsyncApiConfigReader
from asyncapi.spec.transformer.reference_resolver import ReferenceResolvingAsyncAPIObjectTransformer


class CLIContainer(DeclarativeContainer):
    config_path = Provider[Path]()
    config_source = Provider[t.TextIO]()
    config_transformers = Callable(
        lambda path: (ReferenceResolvingAsyncAPIObjectTransformer(""),),
        config_path.provided,
    )

    reader: KeySelector[AsyncApiConfigReader] = KeySelector(
        {
            ".yml": Singleton(YamlAsyncApiConfigReader),
            ".yaml": Singleton(YamlAsyncApiConfigReader),
            ".json": Singleton(JsonAsyncApiConfigReader),
        },
        config_path.provided.suffix,
    )
    config = Callable(
        read_config,
        source=config_source,
        reader=reader,
        transformers=config_transformers,
    )
    generator: KeySelector[AsyncApiCodeGenerator] = KeySelector({
        "python-aio-pika": Singleton(JinjaBasedPythonAioPikaCodeGenerator),
    })


@click.group("cli")
@click.option(
    "-f", "--file",
    type=click.Path(exists=True, path_type=Path),
    default=Path.cwd() / "asyncapi.yaml",
)
@click.pass_context
def cli(context: click.Context, file: Path) -> None:
    container = context.obj = CLIContainer()

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
@click.argument("format", type=click.Choice(sorted(CLIContainer.generator.keys)))
@click.option("-o", "--output-dir", type=click.Path(exists=True, path_type=Path), default=Path.cwd(), )
@click.pass_obj
def generate_code(container: CLIContainer, format: str, output_dir: Path) -> None:
    generator = container.generator(format)
    config = container.config()

    # TODO: add `--dry-run` option
    for destination_path, content in generator.generate(config):
        click.echo(f"generating '{destination_path}' module")

        with output_dir.joinpath(destination_path).open("w") as fd:
            for chunk in content:
                fd.write(chunk)


if __name__ == "__main__":
    cli()
