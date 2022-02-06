import typing as t
from pathlib import Path

from pytest_cases import filters, parametrize_with_cases

from tests.cli import CliInput, CliOutput, CliRunner
from tests.configs.config_complex_message_json_schema.cases import ComplexMessageJsonSchemaConfigCases
from tests.configs.config_temperature_reading.cases import TemperatureReadingsConfigCases

_CASES = (
    ComplexMessageJsonSchemaConfigCases,
    TemperatureReadingsConfigCases,
)


@parametrize_with_cases(("input_", "output",), cases=_CASES)
def test_cli_exit_code(
        cli_runner: CliRunner,
        input_: CliInput,
        output: CliOutput,
) -> None:
    result = cli_runner(input_)

    assert result.exit_code == output.exit_code


@parametrize_with_cases(("input_", "output",), cases=_CASES)
def test_cli_output(
        cli_runner: CliRunner,
        input_: CliInput,
        output: CliOutput,
) -> None:
    result = cli_runner(input_)

    assert result.stdout[:-1] == output.stdout


@parametrize_with_cases(("input_", "output",), cases=_CASES, filter=~filters.has_tags("codegen"))
def test_cli_no_codegen(
        dir_files_loader: t.Callable[[Path], t.Mapping[Path, str]],
        target_dir: Path,
        cli_runner: CliRunner,
        input_: CliInput,
        output: object,
) -> None:
    assert not dir_files_loader(target_dir)

    cli_runner(input_)

    assert not dir_files_loader(target_dir)


@parametrize_with_cases(("input_", "output", "codegen_content",), cases=_CASES, filter=filters.has_tags("codegen"))
def test_cli_codegen(
        dir_files_loader: t.Callable[[Path], t.Mapping[Path, str]],
        target_dir: Path,
        cli_runner: CliRunner,
        input_: CliInput,
        output: object,
        codegen_content: t.Mapping[Path, str],
) -> None:
    assert not dir_files_loader(target_dir)

    cli_runner(input_)

    assert dir_files_loader(target_dir) == codegen_content
