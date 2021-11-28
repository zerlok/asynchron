__all__ = (
    "cli",
)

import typing as t
from contextlib import closing
from pathlib import Path

import click
from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Callable, Object, Provider, Singleton

from asyncapi_python_aio_pika_template.app import (
    AsyncApiCodeGenerator,
    AsyncApiConfigReader,
    read_config,
)
from asyncapi_python_aio_pika_template.generator.jinja.python_aio_pika import JinjaBasedPythonAioPikaCodeGenerator
from asyncapi_python_aio_pika_template.providers import KeySelector
from asyncapi_python_aio_pika_template.reader.json import JsonAsyncApiConfigReader
from asyncapi_python_aio_pika_template.reader.yaml import YamlAsyncApiConfigReader
from asyncapi_python_aio_pika_template.transform.reference_resolver import ReferenceResolvingAsyncAPIObjectTransformer


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
    click.echo(config.json(exclude_none=not show_null, indent=2 if pretty else None,
                           separators=(", ", ": ") if pretty else (",", ":")))


@cli.command("generate")
@click.argument("format", type=click.Choice(sorted(CLIContainer.generator.keys)))
@click.pass_obj
def generate_code(container: CLIContainer, format: str) -> None:
    config = container.config()
    # generator = container.generator(format)
    #
    # for destination_path, content in generator.generate(config):
    #     click.echo(destination_path)
    #     click.echo(content)

    # for obj in BFSWalker(config):
    #     if obj.key == "publish":
    #         resolver = RefResolver("", config)
    #         print(resolver)
    #         print(obj)
    #         # print(resolver.resolve(obj.value.message.ref))
    #


if __name__ == "__main__":
    cli()
