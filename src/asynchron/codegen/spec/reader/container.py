__all__ = (
    "ConfigReaderContainer",
)

import typing as t
from pathlib import Path

from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Callable, Factory, List, Provider, Singleton

from asynchron.codegen.app import AsyncApiConfigReader, AsyncApiConfigTransformer
from asynchron.codegen.spec.reader.json import JsonAsyncApiConfigReader
from asynchron.codegen.spec.reader.transformer import AsyncApiConfigTransformingConfigReader
from asynchron.codegen.spec.reader.yaml import YamlAsyncApiConfigReader
from asynchron.codegen.spec.transformer.json_reference_resolver import JsonReferenceResolvingTransformer
from asynchron.providers import MappingValueSelector


def _create_json_reference_resolving_config_reader(
        reader: AsyncApiConfigReader,
        path: Path,
        json_resolving_transformer_factory: t.Callable[[Path], AsyncApiConfigTransformer],
) -> AsyncApiConfigReader:
    return AsyncApiConfigTransformingConfigReader(reader, [json_resolving_transformer_factory(path), ])


class ConfigReaderContainer(DeclarativeContainer):
    yaml: Provider[AsyncApiConfigReader] = Singleton(YamlAsyncApiConfigReader)
    json: Provider[AsyncApiConfigReader] = Singleton(JsonAsyncApiConfigReader)

    format_specific: Provider[AsyncApiConfigReader] = MappingValueSelector({
        "yml": yaml,
        "yaml": yaml,
        "json": json,
    })

    json_reference_resolving_config_transformer: Provider[JsonReferenceResolvingTransformer] = Factory(
        JsonReferenceResolvingTransformer,
    )
    json_reference_resolved: Provider[AsyncApiConfigReader] = Callable(
        _create_json_reference_resolving_config_reader,
        json_resolving_transformer_factory=json_reference_resolving_config_transformer.provider,
    )

    # FIXME: Incompatible types in assignment (expression has type "dependency_injector.providers.List", variable has
    #  type "Provider[Sequence[AsyncApiConfigTransformer]]")  [assignment]
    transformers: Provider[t.Sequence[AsyncApiConfigTransformer]] = List()  # type: ignore
    normalized: Provider[AsyncApiConfigReader] = Factory(
        AsyncApiConfigTransformingConfigReader,
        transformers=transformers,
    )
