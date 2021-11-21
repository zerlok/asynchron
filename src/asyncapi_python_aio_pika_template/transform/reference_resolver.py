__all__ = (
    "ReferenceResolvingAsyncAPIObjectTransformer",
)

import typing as t

from jsonschema import RefResolver

from asyncapi_python_aio_pika_template.app import AsyncApiConfigTransformer
from asyncapi_python_aio_pika_template.spec import AsyncAPIObject, ReferenceObject
from asyncapi_python_aio_pika_template.walker.bfs import BFSDescendantSpecObjectWalker


class ReferenceResolvingAsyncAPIObjectTransformer(AsyncApiConfigTransformer):

    def __init__(self, uri: str = "") -> None:
        self.__uri = uri

    def transform(self, config: AsyncAPIObject) -> AsyncAPIObject:
        resolver = RefResolver(self.__uri, config.dict())

        # TODO: replace resolved values in a config copy.
        for ref in self.__iter_references(config):
            _, resolved = resolver.resolve(ref)
            print(ref, resolved)

        return config

    def __iter_references(self, config: AsyncAPIObject) -> t.Iterable[str]:
        for obj in BFSDescendantSpecObjectWalker(config):
            if isinstance(obj.value, ReferenceObject):
                yield obj.value.ref
