import typing as t
from pathlib import Path

import pytest
from pytest_cases import filters, parametrize_with_cases

from tests.cli import CliInput, CliOutput, CliRunner
from tests.configs.config_complex_json_references.cases import (
    ComplexBrokenJsonReferencesConfigCases,
    ComplexJsonReferencesConfigCases,
)
from tests.configs.config_complex_message_json_schema.cases import ComplexMessageJsonSchemaConfigCases
from tests.configs.config_temperature_reading.cases import TemperatureReadingsConfigCases

# TODO: autoload case classes from `case` files.
_CASES = (
    TemperatureReadingsConfigCases,
    ComplexMessageJsonSchemaConfigCases,
    ComplexJsonReferencesConfigCases,
    ComplexBrokenJsonReferencesConfigCases,
)

_TAG_CODEGEN = filters.has_tags("codegen")
_TAG_EXCEPTION = filters.has_tags("exception")


@parametrize_with_cases(("input_", "output",), cases=_CASES, filter=~_TAG_EXCEPTION)
def test_cli_normal_run_with_expected_output(
        cli_runner: CliRunner,
        input_: CliInput,
        output: CliOutput,
) -> None:
    result = cli_runner(input_)

    assert not result.stderr
    assert result.exit_code == output.exit_code
    assert result.stdout[:-1] == output.stdout


@parametrize_with_cases(("input_", "exception",), cases=_CASES, filter=_TAG_EXCEPTION)
def test_cli_raises_exception(
        cli_runner: CliRunner,
        input_: CliInput,
        exception: t.Type[BaseException],
) -> None:
    with pytest.raises(exception):
        cli_runner(input_)


@parametrize_with_cases(("input_", "output",), cases=_CASES, filter=~_TAG_CODEGEN & ~_TAG_EXCEPTION)
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


@parametrize_with_cases(("input_", "output", "codegen_content",), cases=_CASES, filter=_TAG_CODEGEN)
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
