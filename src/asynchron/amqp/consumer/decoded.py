__all__ = (
    "DecodedMessageConsumer",
)

import typing as t

import aio_pika

from asynchron.amqp.base import ConsumptionContext, MessageConsumer, MessageDecoder

T_contra = t.TypeVar("T_contra", contravariant=True)


class DecodedMessageConsumer(MessageConsumer[aio_pika.IncomingMessage]):
    def __init__(self, consumer: MessageConsumer[T_contra], decoder: MessageDecoder[T_contra]) -> None:
        self.__consumer = consumer
        self.__decoder = decoder

    async def consume(self, message: aio_pika.IncomingMessage, context: ConsumptionContext) -> None:
        decoded_message = self.__decoder.decode(message, context)
        await self.__consumer.consume(decoded_message, context)
