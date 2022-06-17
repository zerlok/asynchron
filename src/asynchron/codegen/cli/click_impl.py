__all__ = (
    "cli",
)

import typing as t
from contextlib import closing
from pathlib import Path

import click
from dependency_injector.providers import (
    Callable,
    Object,
)

from asynchron.codegen.cli.container import CLIContainer
from asynchron.strict_typing import as_


def _load_config_source(path: Path, context: click.Context) -> t.TextIO:
    return context.with_resource(closing(path.open("r")))


@click.group("cli")
@click.option(
    "-f", "--file", "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=Path.cwd() / "asyncapi.yaml",
)
@click.pass_context
def cli(context: click.Context, config_path: Path) -> None:
    container = as_(CLIContainer, context.obj)
    if container is None:
        container = context.obj = CLIContainer(
            stdout=Callable(click.get_text_stream, name="stdout"),
            config_source_loader=Callable(_load_config_source, context=context),
        )

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
        container.config_view_settings.add_kwargs(
            show_null=show_null,
            prettified=pretty,
            indent=indent,
            sort_keys=sort_keys,
        )

    if not enable_normalize:
        container.config_titles_normalizer.override(container.config_null_transformer)


@cli.command("codegen")
@click.argument("format", type=click.Choice(sorted(CLIContainer.code_generator.keys)))
@click.option("-o", "--output-dir", type=click.Path(exists=False, path_type=Path), default=Path.cwd(), )
@click.option("-p", "--project", type=str, default=None, )
@click.option("-d", "--dry-run", is_flag=True, default=False)
@click.option("--enable-main/--disable-main", is_flag=True, default=True)
@click.option("--enable-meta/--disable-meta", is_flag=True, default=True)
@click.option("--ignore-formatter/--allow-formatter", is_flag=True, default=True)
@click.option("--use-absolute-imports/--use-relative-imports", is_flag=True, default=False)
@click.pass_obj
def codegen(
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

    # FIXME: "Provider[Any]" has no attribute "add_kwargs"  [attr-defined]
    container.code_generators.meta_info.add_kwargs(  # type: ignore
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
