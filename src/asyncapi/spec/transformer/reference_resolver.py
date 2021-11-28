__all__ = (
    "ReferenceResolvingAsyncAPIObjectTransformer",
)

import itertools as it
import typing as t

from jsonschema import RefResolutionError, RefResolver

from asyncapi.app import AsyncApiConfigTransformer, AsyncApiConfigTransformerError
from asyncapi.spec.base import AsyncAPIObject, ReferenceObject, SpecObject
from asyncapi.spec.visitor.referenced_descendants import (
    ReferencedDescendantSpecObjectVisitor,
    ReferencedSpecObject,
)
from asyncapi.spec.walker.bfs_path import BFSPathWalker

JsonReference = t.NewType("JsonReference", str)
JsonPath = t.Sequence[t.Union[int, str]]


class JsonSerializable(t.Protocol):
    def __getitem__(self, item: t.Union[int, str]) -> "JsonSerializable": ...

    def __setitem__(self, item: t.Union[int, str], value: "JsonSerializable") -> "JsonSerializable": ...


class ReferenceResolvingAsyncAPIObjectTransformer(AsyncApiConfigTransformer):

    def __init__(self, uri: str = "", max_iterations: int = 256) -> None:
        if not (0 < max_iterations <= 256):
            raise ValueError("Max iterations not in valid values range", max_iterations)

        self.__uri = uri
        self.__max_iterations = max_iterations
        self.__spec_object_descendants_visitor = ReferencedDescendantSpecObjectVisitor()

    def transform(self, config: AsyncAPIObject) -> AsyncAPIObject:
        cfg = config

        # TODO: get total reference graph and resolve it ordering by dependencies or cancel resolution if graph has
        #  cycles.
        for _ in self.__iter_max_iterations():
            cfg_json = t.cast(JsonSerializable, cfg.dict(by_alias=True))
            resolver = _JsonReferenceResolver(cfg_json)
            references = list(self.__iter_references(cfg))
            if not references:
                break

            for json_ref, json_path in references:
                self.__assign_json_value(cfg_json, json_path, resolver(json_ref))

            # FIXME: idk, why mypy fails
            #    error: Expression type contains "Any" (has type "Type[AsyncAPIObject]")  [misc]
            cfg = AsyncAPIObject.parse_obj(cfg_json)  # type: ignore[misc]

        return cfg

    def __get_spec_object_descendants(self, obj: ReferencedSpecObject) -> t.Sequence[ReferencedSpecObject]:
        return obj.value.accept_visitor(self.__spec_object_descendants_visitor)

    def __iter_max_iterations(self) -> t.Iterable[int]:
        for i in range(self.__max_iterations):
            yield i

        else:
            raise RuntimeError("Iteration limits on reference resolving is exceeded", self.__max_iterations)

    def __iter_references(self, config: SpecObject) -> t.Iterable[t.Tuple[JsonReference, JsonPath]]:
        for path in BFSPathWalker(ReferencedSpecObject((), config), self.__get_spec_object_descendants):
            value = path.value.value
            # FIXME: mypy can't infer the type of `value`
            #  error: Expression type contains "Any" (has type "Type[ReferenceObject]")  [misc]
            if isinstance(value, ReferenceObject):  # type: ignore[misc]
                yield JsonReference(value.ref), tuple(it.chain.from_iterable(part.ref for part in path.parts))

    def __assign_json_value(self, cfg_json: JsonSerializable, json_path: JsonPath, value: JsonSerializable) -> None:
        target = cfg_json
        *parts, last = json_path

        for part in parts:
            target = target[part]

        target[last] = value


class _JsonReferenceResolver:
    def __init__(self, data: JsonSerializable) -> None:
        self.__resolver = RefResolver.from_schema(data)  # type: ignore

    def __call__(self, ref: str) -> JsonSerializable:
        try:
            _, resolved_value = self.__resolver.resolve(ref)  # type: ignore

        except t.cast(t.Type[Exception], RefResolutionError) as err:
            raise AsyncApiConfigTransformerError("Json reference resolving failed", ref)

        else:
            return t.cast(JsonSerializable, resolved_value)
