import json
import typing as t
from pathlib import Path

from pytest_cases import case

from tests.cli import CliInput, CliOutput
from tests.configs.config import CodegenConfig, use_codegen_config_from_dir_as_fixture


@use_codegen_config_from_dir_as_fixture(Path(__file__).parent)
class ComplexJsonReferencesConfigCases:

    @case(tags=("cli",), )
    def case_read_config_in_pretty_format(
            self,
            config: CodegenConfig,
    ) -> t.Tuple[CliInput, CliOutput]:
        return (
            CliInput(
                args=("-f", str(config.asyncapi_config_path), "get", "--pretty",),
            ),
            CliOutput(
                stdout=json.dumps(config.normalized_config, indent=2, separators=(", ", ": "), sort_keys=True),
            ),
        )
