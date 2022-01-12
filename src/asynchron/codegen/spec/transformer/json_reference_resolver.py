__all__ = (
    "JsonReferenceResolvingTransformer",
)

import typing as t

from jsonschema import RefResolutionError, RefResolver

from asynchron.codegen.app import AsyncApiConfigTransformer, AsyncApiConfigTransformerError
from asynchron.codegen.spec.base import AsyncAPIObject, ReferenceObject, SpecObject
from asynchron.codegen.spec.walker.spec_object_path import SpecObjectPath, SpecObjectWithPathWalker
from asynchron.serializable_object_modifier import SerializableObjectModifier
from asynchron.strict_typing import SerializableObject, as_

JsonReference = t.NewType("JsonReference", str)


class JsonReferenceResolvingTransformer(AsyncApiConfigTransformer):

    def __init__(
            self,
            modifier: t.Optional[SerializableObjectModifier] = None,
            max_iterations: int = 256,
    ) -> None:
        if not (0 < max_iterations <= 256):
            raise ValueError("Max iterations not in valid values range", max_iterations)

        self.__modifier = modifier or SerializableObjectModifier()
        self.__max_iterations = max_iterations
        self.__walker = SpecObjectWithPathWalker.create_bfs()

    def transform(self, config: AsyncAPIObject) -> AsyncAPIObject:
        cfg = config

        # TODO: get total reference graph and resolve it ordering by dependencies or cancel resolution if graph has
        #  cycles.
        for _ in self.__iter_max_iterations():
            resolver = _AsyncAPIObjectJsonReferenceResolver(cfg)
            references = list(self.__iter_references(cfg))
            if not references:
                break

            cfg = self.__modifier.replace(
                target=cfg,
                changes=[
                    (obj_path, resolver(json_ref))
                    for json_ref, obj_path in references
                ],
            )

        return cfg

    def __iter_max_iterations(self) -> t.Iterable[int]:
        for i in range(self.__max_iterations):
            yield i

        else:
            raise RuntimeError("Iteration limits on reference resolving is exceeded", self.__max_iterations)

    def __iter_references(self, config: SpecObject) -> t.Iterable[t.Tuple[JsonReference, SpecObjectPath]]:
        for path, value in self.__walker.walk(config):
            # FIXME: mypy can't infer the type of `value`
            #  error: Expression type contains "Any" (has type "Type[ReferenceObject]")  [misc]
            if ref_obj := as_(ReferenceObject, value):  # type: ignore[misc]
                yield JsonReference(ref_obj.ref), path


class _AsyncAPIObjectJsonReferenceResolver:
    def __init__(self, data: AsyncAPIObject) -> None:
        self.__resolver = RefResolver.from_schema(data.dict(by_alias=True, exclude_none=True))  # type: ignore

    def __call__(self, ref: str) -> SerializableObject:
        try:
            _, resolved_value = self.__resolver.resolve(ref)  # type: ignore

        except t.cast(t.Type[Exception], RefResolutionError) as err:
            raise AsyncApiConfigTransformerError("Json reference resolving failed", ref)

        else:
            return t.cast(SerializableObject, resolved_value)
