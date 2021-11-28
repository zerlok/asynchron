__all__ = (
    "CallableMessageConsumer",
)

import typing as t

from asyncapi.amqp.base import ConsumptionContext, MessageConsumer

T_contra = t.TypeVar("T_contra", contravariant=True)


class CallableMessageConsumer(MessageConsumer[T_contra]):
    def __init__(self, consumer: t.Callable[[T_contra, ConsumptionContext], t.Awaitable[None]]) -> None:
        self.__consumer = consumer

    async def consume(self, message: T_contra, context: ConsumptionContext) -> None:
        await self.__consumer(message, context)
