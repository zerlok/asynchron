import json
import typing as t
from pathlib import Path

from click.testing import CliRunner
from pytest_cases import fixture, parametrize_with_cases

from asyncapi.cli import cli


@fixture()
def data_dir() -> Path:
    return Path(__file__).parent / "data"


@fixture()
def cli_runner() -> CliRunner:
    return CliRunner()


class ConfigCases:
    def case_config_001(self, data_dir: Path) -> t.Tuple[Path, t.Any]:
        with (data_dir / "config-001" / "final.json").open("r") as fd:
            config_json = json.load(fd)

        return data_dir / "config-001" / "asyncapi.yaml", config_json


# TODO: i want to do less copy-past for parametrizing tests with `ConfigCases`
class CliCases:
    @parametrize_with_cases(("config_path", "config_json"), ConfigCases)
    def case_read_config_in_compact_format(
            self,
            config_path: Path,
            config_json: t.Any,
    ) -> t.Tuple[t.Mapping[str, t.Any], t.Sequence[t.Any], int, str]:
        return {}, ("-f", str(config_path), "get",), 0, json.dumps(config_json, indent=None, separators=(",", ":"),
                                                                   sort_keys=True)

    @parametrize_with_cases(("config_path", "config_json"), ConfigCases)
    def case_read_config_in_pretty_format(
            self,
            config_path: Path,
            config_json: t.Any,
    ) -> t.Tuple[t.Mapping[str, t.Any], t.Sequence[t.Any], int, str]:
        return {}, ("-f", str(config_path), "get", "--pretty"), 0, json.dumps(config_json, indent=2,
                                                                              separators=(", ", ": "), sort_keys=True)


@parametrize_with_cases(("env", "args", "expected_exit_code", "expected_output",), (CliCases,))
def test_cli(
        cli_runner: CliRunner,
        env: t.Mapping[str, t.Any],
        args: t.Sequence[t.Any],
        expected_exit_code: int,
        expected_output: str,
) -> None:
    result = cli_runner.invoke(cli, args=args, env=env)

    assert (result.exit_code, result.stdout) == (expected_exit_code, f"{expected_output}\n")
