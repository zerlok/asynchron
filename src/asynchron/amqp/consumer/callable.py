__all__ = (
    "CallableMessageConsumer",
    "CallableInvokingMessageConsumer",
)

import typing as t

from asynchron.amqp.base import ConsumptionContext, MessageConsumer

T_contra = t.TypeVar("T_contra", contravariant=True)


class CallableMessageConsumer(t.Protocol[T_contra]):
    async def __call__(self, message: T_contra, context: ConsumptionContext) -> None: ...


class CallableInvokingMessageConsumer(MessageConsumer[T_contra]):
    def __init__(self, consumer: CallableMessageConsumer[T_contra]) -> None:
        self.__consumer = consumer

    async def consume(self, message: T_contra, context: ConsumptionContext) -> None:
        await self.__consumer(message, context)
