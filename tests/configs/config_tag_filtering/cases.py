import typing as t
from pathlib import Path

from pytest_cases import case

from tests.cli import CliInput, CliOutput
from tests.configs.config import CodegenConfig, use_codegen_config_from_dir_as_fixture


@use_codegen_config_from_dir_as_fixture(Path(__file__).parent, generated_code_dir="generated_one")
class TagOneFilterCases:

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
                    "generate", "python-aio-pika",
                    "-o", str(target_dir),
                    "-p", project_name,
                    "--operation-tags", "one",
                    "--disable-meta", "--ignore-formatter", "--use-relative-imports",
                ),
            ),
            CliOutput(),
            config.generated_code_file_content,
        )


@use_codegen_config_from_dir_as_fixture(Path(__file__).parent, generated_code_dir="generated_two_three")
class TagTwoThreeFilterCases:

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
                    "generate", "python-aio-pika",
                    "-o", str(target_dir),
                    "-p", project_name,
                    "--operation-tags", "two",
                    "--operation-tags", "three",
                    "--disable-meta", "--ignore-formatter", "--use-relative-imports",
                ),
            ),
            CliOutput(),
            config.generated_code_file_content,
        )
