__all__ = (
    "NullTransformer",
)

from asynchron.codegen.app import AsyncApiConfigTransformer
from asynchron.codegen.spec.asyncapi import AsyncAPIObject


class NullTransformer(AsyncApiConfigTransformer):

    def transform(self, config: AsyncAPIObject) -> AsyncAPIObject:
        return config
