__all__ = (
    "cli",
)

import typing as t
from contextlib import closing
from pathlib import Path

import click
from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Callable, Object, Provider, Selector, Singleton

from asyncapi_python_aio_pika_template.app import AsyncApiCodeGenerator, AsyncApiConfigReader
from asyncapi_python_aio_pika_template.generator.jinja.python_aio_pika import JinjaBasedPythonAioPikaCodeGenerator
from asyncapi_python_aio_pika_template.reader.json import JsonAsyncApiConfigReader
from asyncapi_python_aio_pika_template.reader.yaml import YamlAsyncApiConfigReader
from asyncapi_python_aio_pika_template.spec import AsyncAPIObject


class CLIContainer(DeclarativeContainer):
    config = Provider[AsyncAPIObject]()

    reader_type = Provider[str]()
    reader: Provider[AsyncApiConfigReader] = Selector(
        reader_type,
        yml=Singleton(YamlAsyncApiConfigReader),
        yaml=Singleton(YamlAsyncApiConfigReader),
        json=Singleton(JsonAsyncApiConfigReader),
    )

    generator_type = Provider[str]()
    generator: Provider[AsyncApiCodeGenerator] = Selector(
        generator_type,
        # python_aio_pika=Singleton(JinjaBasedPythonAioPikaCodeGenerator),
    )


def make_command_invoker(
        name: str,
        parent: t.Optional[click.Group] = None,
        commands: t.Optional[t.Sequence[click.Command]] = None,
) -> t.Callable[[t.Callable[[CLIContainer], None]], click.Group]:
    def wrap(func: t.Callable[[CLIContainer], None]) -> click.Group:
        @click.pass_obj
        def perform(container: CLIContainer, _: object) -> None:
            return func(container)

        group = click.Group(
            name=name,
            commands=commands,
            result_callback=perform,
            invoke_without_command=True,
        )

        if parent is not None:
            parent.add_command(group)

        return group

    return wrap


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
        reader = container.reader()
        return reader.read(context.with_resource(closing(path.open("r"))))

    container.reader_type.override(Object(config.suffix[1:]))
    container.config.override(Callable(read_config, config))


@cli.command("get")
@click.option("--pretty/--compact", is_flag=True, default=False)
@click.option("--show-null/--no-null", default=False)
@click.pass_obj
def get_config(container: CLIContainer, pretty: bool, show_null: bool) -> None:
    config = container.config()
    click.echo(config.json(exclude_none=not show_null, indent=2 if pretty else None,
                           separators=(", ", ": ") if pretty else (",", ":")))


@make_command_invoker("generate", cli)
def generate_code(container: CLIContainer) -> None:
    config = container.config()
    generator = container.generator()

    for destination_path, content in generator.generate(config):
        print(destination_path, content)


if __name__ == "__main__":
    cli()
