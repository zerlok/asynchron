import json
import typing as t
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from click.testing import CliRunner, Result
from dependency_injector.providers import Object
from pytest_cases import case, fixture, parametrize_with_cases

from asynchron.spec.cli import CLIContainer, cli


@dataclass(frozen=True)
class CliInput:
    obj: t.Optional[CLIContainer] = None
    args: t.Sequence[str] = field(default_factory=tuple)
    env: t.Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CliOutput:
    exit_code: int = 0
    stdout: str = ""
    files_content: t.Mapping[Path, t.Sequence[str]] = field(default_factory=dict)


@fixture()
def data_dir() -> Path:
    return Path(__file__).parent / "data"


@fixture()
def cli_runner() -> t.Callable[[CliInput], Result]:
    runner = CliRunner()

    def run(input: CliInput) -> Result:
        # noinspection PyTypeChecker
        return runner.invoke(
            cli=cli,
            obj=input.obj,
            args=input.args,
            env=input.env,
        )

    return run


@fixture()
def target_dir(tmp_path: Path) -> Path:
    return tmp_path


@fixture()
def file_content_loader() -> t.Callable[[Path], t.Mapping[Path, t.Sequence[str]]]:
    def walk_file_paths(root: Path) -> t.Iterable[Path]:
        paths: t.List[Path] = [root]
        while paths:
            path = paths.pop(0)
            if path.is_dir():
                paths.extend(path.iterdir())

            if path.is_file():
                yield path

    def load_file(path: Path) -> str:
        with path.open("r") as fd:
            return "\n".join(line for line in (line.strip() for line in fd) if line)[:100]

    def load_dir(root: Path) -> t.Mapping[Path, t.Sequence[str]]:
        results = {}

        for path in walk_file_paths(root):
            results[Path(*path.parts[len(root.parts):])] = load_file(path)

        # noinspection PyTypeChecker
        return OrderedDict(sorted(results.items(), key=lambda pair: str(pair[0])))

    return load_dir


class ConfigCases:
    def case_config_001(
            self,
            data_dir: Path,
            file_content_loader: t.Callable[[Path], t.Mapping[Path, t.Sequence[str]]],
    ) -> t.Tuple[Path, t.Any, t.Mapping[Path, t.Sequence[str]], str]:
        root = data_dir / "config-001"

        with (root / "final.json").open("r") as fd:
            config_json = json.load(fd)

        return root / "asyncapi.yaml", config_json, file_content_loader(root / "final_code"), "config_001"


class CurrentTimeCases:
    def case_2021_01_01_00_00_00(self) -> datetime:
        return datetime(2021, 1, 1, 0, 0, 0)

    def case_2021_02_03_04_05_06_789(self) -> datetime:
        return datetime(2021, 2, 3, 4, 5, 6, 789)

    def case_2021_12_31_23_59_59_999(self) -> datetime:
        return datetime(2021, 12, 31, 23, 59, 59, 999)

    def case_2345_06_17_18_19_20(self) -> datetime:
        return datetime(2345, 6, 17, 18, 19, 20)


# TODO: i want to do less copy-past for parametrizing tests with `ConfigCases`
class CliCases:
    @parametrize_with_cases(("config_path", "config_json",), ConfigCases)
    @case(tags=("read", "compact", "success", "has-output",), )
    def case_read_config_in_compact_format(
            self,
            config_path: Path,
            config_json: t.Any,
    ) -> t.Tuple[CliInput, CliOutput]:
        return (
            CliInput(
                args=("-f", str(config_path), "get",),
            ),
            CliOutput(
                stdout=json.dumps(config_json, indent=None, separators=(",", ":"), sort_keys=True),
            ),
        )

    @parametrize_with_cases(("config_path", "config_json",), ConfigCases)
    @case(tags=("read", "pretty", "success", "has-output",), )
    def case_read_config_in_pretty_format(
            self,
            config_path: Path,
            config_json: t.Any,
    ) -> t.Tuple[CliInput, CliOutput]:
        return (
            CliInput(
                args=("-f", str(config_path), "get", "--pretty",),
            ),
            CliOutput(
                stdout=json.dumps(config_json, indent=2, separators=(", ", ": "), sort_keys=True),
            ),
        )

    @parametrize_with_cases(("now",), CurrentTimeCases)
    @parametrize_with_cases(("config_path", "config_json", "project_file_content", "project_name",), ConfigCases)
    @case(tags=("generate", "python-aio-pika", "success", "fs-changes",), )
    def case_generate_python_aio_pika_app_code_from_config(
            self,
            now: datetime,
            config_path: Path,
            config_json: t.Any,
            project_name: t.Any,
            project_file_content: t.Mapping[Path, t.Sequence[str]],
            target_dir: Path,
    ) -> t.Tuple[CliInput, CliOutput]:
        return (
            CliInput(
                obj=CLIContainer(
                    now=Object(now),
                ),
                args=(
                    "-f", str(config_path), "generate", "python-aio-pika", "-o", str(target_dir), "-p", project_name,
                ),
            ),
            CliOutput(
                files_content=project_file_content,
            ),
        )


@parametrize_with_cases(("input", "output",), (CliCases,), )
def test_cli_exit_code(
        cli_runner: t.Callable[[CliInput], Result],
        input: CliInput,
        output: CliOutput,
) -> None:
    result = cli_runner(input)

    assert result.exit_code == output.exit_code


@parametrize_with_cases(("input", "output",), (CliCases,), )
def test_cli_output(
        cli_runner: t.Callable[[CliInput], Result],
        input: CliInput,
        output: CliOutput,
) -> None:
    result = cli_runner(input)

    assert result.stdout[:-1] == output.stdout

# FIXME: fix code gen (clean output format)
# @parametrize_with_cases(("input", "output",), (CliCases,), )
# def test_cli_fs_changes(
#         cli_runner: t.Callable[[CliInput], Result],
#         input: CliInput,
#         output: CliOutput,
#         target_dir: Path,
#         file_content_loader: t.Callable[[Path], t.Mapping[Path, t.Sequence[str]]],
# ) -> None:
#     assert not file_content_loader(target_dir)
#
#     cli_runner(input)
#
#     assert file_content_loader(target_dir) == output.files_content
