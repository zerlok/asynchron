__all__ = (
    "SpecObjectTransformer",
)

import typing as t

from asynchron.codegen.app import AsyncApiConfigTransformer
from asynchron.codegen.spec.asyncapi import AsyncAPIObject, SpecObject
from asynchron.codegen.spec.walker.base import Walker
from asynchron.codegen.spec.walker.spec_object_path import SpecObjectPath, SpecObjectWithPathWalker
from asynchron.serializable_object_modifier import SerializableObjectModifier


class SpecObjectTransformer(AsyncApiConfigTransformer):

    def __init__(
            self,
            transformer: t.Callable[[SpecObjectPath, SpecObject], t.Optional[SpecObject]],
            modifier: t.Optional[SerializableObjectModifier] = None,
            walker: t.Optional[Walker[SpecObject, t.Tuple[SpecObjectPath, SpecObject]]] = None,
    ) -> None:
        self.__transformer = transformer
        self.__modifier = modifier or SerializableObjectModifier()
        self.__walker = walker or SpecObjectWithPathWalker.create_dfs_pre_ordering()

    def transform(self, config: AsyncAPIObject) -> AsyncAPIObject:
        changes: t.List[t.Tuple[t.Sequence[t.Union[int, str]], t.Optional[SpecObject]]] = []

        for path, obj in self.__walker.walk(config):
            transformed_obj = self.__transformer(path, obj)
            if transformed_obj != obj:
                changes.append((path, transformed_obj))

        return self.__modifier.replace(config, changes)
