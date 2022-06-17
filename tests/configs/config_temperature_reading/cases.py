import json
import typing as t
from pathlib import Path

from pytest_cases import case

from tests.cli import CliInput, CliOutput
from tests.configs.config import CodegenConfig, use_codegen_config_from_dir_as_fixture


@use_codegen_config_from_dir_as_fixture(Path(__file__).parent)
class TemperatureReadingsConfigCases:

    @case(tags=("cli",), )
    def case_read_config_in_compact_format(
            self,
            config: CodegenConfig,
    ) -> t.Tuple[CliInput, CliOutput]:
        return (
            CliInput(
                args=("-f", str(config.asyncapi_config_path), "config",),
            ),
            CliOutput(
                stdout=json.dumps(config.normalized_config, indent=None, separators=(",", ":"), sort_keys=True),
            ),
        )

    @case(tags=("cli",), )
    def case_read_config_in_pretty_format(
            self,
            config: CodegenConfig,
    ) -> t.Tuple[CliInput, CliOutput]:
        return (
            CliInput(
                args=("-f", str(config.asyncapi_config_path), "config", "--pretty",),
            ),
            CliOutput(
                stdout=json.dumps(config.normalized_config, indent=2, separators=(", ", ": "), sort_keys=True),
            ),
        )

    @case(tags=("cli", "codegen",), )
    def case_generate_python_aio_pika_app_code_from_config(
            self,
            config: CodegenConfig,
            project_name: str,
            target_dir: Path,
    ) -> t.Tuple[CliInput, CliOutput, t.Mapping[Path, str]]:
        return (
            CliInput(
                args=(
                    "-f", str(config.asyncapi_config_path),
                    "codegen", "python-aio-pika",
                    "-o", str(target_dir),
                    "-p", project_name,
                    "--disable-meta", "--ignore-formatter", "--use-relative-imports",
                ),
            ),
            CliOutput(),
            config.generated_code_file_content,
        )
