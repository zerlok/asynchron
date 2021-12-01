import json
import typing as t
from dataclasses import dataclass, field
from pathlib import Path

from click.testing import CliRunner
from pytest_cases import case, fixture, parametrize_with_cases

from asyncapi.cli import cli


@dataclass(frozen=True)
class CliInput:
    args: t.Sequence[str] = field(default_factory=tuple)
    env: t.Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CliOutput:
    exit_code: int = 0
    stdout: str = ""
    fs_changes: t.Mapping[Path, t.Sequence[str]] = field(default_factory=dict)


@fixture()
def data_dir() -> Path:
    return Path(__file__).parent / "data"


@fixture()
def cli_runner() -> CliRunner:
    return CliRunner()


@fixture()
def target_dir(tmpdir: str) -> Path:
    return Path(tmpdir)


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

    def load_dir(root: Path) -> t.Mapping[Path, t.Sequence[str]]:
        results = {}

        for path in walk_file_paths(root):
            with path.open("r") as fd:
                results[Path(*path.parts[len(root.parts):])] = fd.readlines()

        return results

    return load_dir


class ConfigCases:
    def case_config_001(
            self,
            data_dir: Path,
            file_content_loader: t.Callable[[Path], t.Mapping[Path, t.Sequence[str]]],
    ) -> t.Tuple[Path, t.Any, t.Mapping[Path, t.Sequence[str]]]:
        root = data_dir / "config-001"

        with (root / "final.json").open("r") as fd:
            config_json = json.load(fd)

        return root / "asyncapi.yaml", config_json, file_content_loader(root / "final_code")


# TODO: i want to do less copy-past for parametrizing tests with `ConfigCases`
class CliCases:
    @parametrize_with_cases(("config_path", "config_json"), ConfigCases)
    @case(tags=("read", "compact", "success", "has-output"))
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

    @parametrize_with_cases(("config_path", "config_json"), ConfigCases)
    @case(tags=("read", "pretty", "success", "has-output"))
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

    @parametrize_with_cases(("config_path", "config_json", "project_file_content"), ConfigCases)
    @case(tags=("generate", "python-aio-pika", "success", "fs-changes",))
    def case_generate_python_aio_pika_app_code_from_config(
            self,
            config_path: Path,
            config_json: t.Any,
            project_file_content: t.Mapping[Path, t.Sequence[str]],
            target_dir: Path,
    ) -> t.Tuple[CliInput, CliOutput]:
        return (
            CliInput(
                args=("-f", str(config_path), "generate", "python-aio-pika", "-o", str(target_dir),),
            ),
            CliOutput(
                fs_changes=project_file_content,
            ),
        )


@parametrize_with_cases(("input", "output",), (CliCases,), )
def test_cli_exit_code(
        cli_runner: CliRunner,
        input: CliInput,
        output: CliOutput,
) -> None:
    result = cli_runner.invoke(cli, args=input.args, env=input.env)

    assert result.exit_code == output.exit_code


@parametrize_with_cases(("input", "output",), (CliCases,), )
def test_cli_output(
        cli_runner: CliRunner,
        input: CliInput,
        output: CliOutput,
) -> None:
    result = cli_runner.invoke(cli, args=input.args, env=input.env)

    assert result.stdout[:-1] == output.stdout


@parametrize_with_cases(("input", "output",), (CliCases,), )
def test_cli_fs_changes(
        cli_runner: CliRunner,
        input: CliInput,
        output: CliOutput,
        target_dir: Path,
        file_content_loader: t.Callable[[Path], t.Mapping[Path, t.Sequence[str]]],
) -> None:
    assert not file_content_loader(target_dir)

    cli_runner.invoke(cli, args=input.args, env=input.env)

    assert file_content_loader(target_dir) == output.fs_changes
