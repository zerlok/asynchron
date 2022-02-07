import json
import typing as t
from pathlib import Path

from pytest_cases import case, parametrize

from asynchron.codegen.app import AsyncApiConfigTransformerError
from tests.cli import CliInput, CliOutput
from tests.configs.config import CodegenConfig, use_codegen_config_from_dir_as_fixture

CONFIG_DIR = Path(__file__).parent


@use_codegen_config_from_dir_as_fixture(CONFIG_DIR, generated_code_dir=None)
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


class ComplexBrokenJsonReferencesConfigCases:

    @parametrize(("asyncapi_config_path",), (
            CONFIG_DIR / "asyncapi-with-json-ref-to-non-existing-attribute-in-external-file.yaml",
            CONFIG_DIR / "asyncapi-with-json-ref-to-non-existing-attribute-in-same-file.yaml",
            CONFIG_DIR / "asyncapi-with-json-ref-to-non-existing-file.yaml",
    ))
    @case(tags=("cli", "exception"), )
    def case_read_config_in_pretty_format(
            self,
            asyncapi_config_path: Path,
    ) -> t.Tuple[CliInput, t.Type[Exception]]:
        assert asyncapi_config_path.exists()

        return (
            CliInput(
                args=("-f", str(asyncapi_config_path), "get", "--pretty",),
            ),
            AsyncApiConfigTransformerError,
            # CliOutput(
            #     stdout=json.dumps(config.normalized_config, indent=2, separators=(", ", ": "), sort_keys=True),
            # ),
        )
