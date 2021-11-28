import abc
import typing as t

import aio_pika

from asyncapi.amqp.base import ConsumptionContext, MessageConsumer, MessageDecoder

T = t.TypeVar("T")


class DecodedMessageConsumer(MessageConsumer[aio_pika.IncomingMessage], metaclass=abc.ABCMeta):
    def __init__(self, consumer: MessageConsumer[T], decoder: MessageDecoder[T]) -> None:
        self.__consumer = consumer
        self.__decoder = decoder

    async def consume(self, message: aio_pika.IncomingMessage, context: ConsumptionContext) -> None:
        decoded_message = self.__decoder.decode(message, context)
        await self.__consumer.consume(decoded_message, context)
