import typing as t
from collections import OrderedDict
from pathlib import Path

import click
from click.testing import CliRunner, Result
from pytest_cases import fixture

from tests.cli import CliInput


@fixture()
def cli_command() -> click.Command:
    from asynchron.codegen.cli.click_impl import cli
    # noinspection PyTypeChecker
    return cli


@fixture()
def cli_runner(cli_command: click.Command) -> t.Callable[[CliInput], Result]:
    runner = CliRunner(mix_stderr=False)

    def run(input_: CliInput) -> Result:
        # noinspection PyTypeChecker
        return runner.invoke(
            cli=cli_command,
            obj=input_.obj,
            args=input_.args,
            env=input_.env,
            catch_exceptions=False,
        )

    return run


@fixture()
def data_dir() -> Path:
    return Path(__file__).parent / "data"


@fixture()
def file_loader() -> t.Callable[[Path], str]:
    def load(path: Path) -> str:
        with path.open("r") as fd:
            return "".join(fd)

    return load


@fixture()
def dir_files_loader(file_loader: t.Callable[[Path], str]) -> t.Callable[[Path], t.Mapping[Path, str]]:
    def walk_file_paths(root: Path) -> t.Iterable[Path]:
        paths: t.List[Path] = [root]
        while paths:
            path = paths.pop(0)
            if path.is_dir():
                paths.extend(path.iterdir())

            if path.is_file():
                yield path

    def load_dir(root: Path) -> t.Mapping[Path, str]:
        results = {}

        for path in walk_file_paths(root):
            results[Path(*path.parts[len(root.parts):])] = file_loader(path)

        # noinspection PyTypeChecker
        return OrderedDict(sorted(results.items(), key=lambda pair: str(pair[0])))

    return load_dir
