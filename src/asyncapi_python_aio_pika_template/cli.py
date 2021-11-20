__all__ = (
    "cli",
)

from contextlib import closing
from pathlib import Path

import click
from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Callable, Provider, Singleton

from asyncapi_python_aio_pika_template.generator.jinja.python_aio_pika import JinjaBasedPythonAioPikaCodeGenerator
from asyncapi_python_aio_pika_template.providers import KeySelector
from asyncapi_python_aio_pika_template.reader.json import JsonAsyncApiConfigReader
from asyncapi_python_aio_pika_template.reader.yaml import YamlAsyncApiConfigReader
from asyncapi_python_aio_pika_template.spec import AsyncAPIObject


class CLIContainer(DeclarativeContainer):
    config = Provider[AsyncAPIObject]()

    reader = KeySelector({
        ".yml": Singleton(YamlAsyncApiConfigReader),
        ".yaml": Singleton(YamlAsyncApiConfigReader),
        ".json": Singleton(JsonAsyncApiConfigReader),
    })
    generator = KeySelector({
        # "python-aio-pika": Singleton(JinjaBasedPythonAioPikaCodeGenerator),
    })


@click.group("cli")
@click.option(
    "-c", "--config",
    type=click.Path(exists=True, path_type=Path),
    default=Path.cwd() / "asyncapi.yaml",
)
@click.pass_context
def cli(context: click.Context, config: Path) -> None:
    container = context.obj = CLIContainer()

    def read_config(path: Path) -> AsyncAPIObject:
        reader = container.reader(path.suffix)
        return reader.read(context.with_resource(closing(path.open("r"))))

    container.config.override(Callable(read_config, config))


@cli.command("get")
@click.option("--pretty/--compact", is_flag=True, default=False)
@click.option("--show-null/--no-null", default=False)
@click.pass_obj
def get_config(container: CLIContainer, pretty: bool, show_null: bool) -> None:
    config = container.config()
    click.echo(config.json(exclude_none=not show_null, indent=2 if pretty else None,
                           separators=(", ", ": ") if pretty else (",", ":")))


@cli.command("generate")
@click.argument("format", type=click.Choice(sorted(CLIContainer.generator.keys())))
@click.pass_obj
def generate_code(container: CLIContainer, format: str) -> None:
    config = container.config()
    generator = container.generator(format)

    for destination_path, content in generator.generate(config):
        click.echo(destination_path)
        click.echo(content)


if __name__ == "__main__":
    cli()
