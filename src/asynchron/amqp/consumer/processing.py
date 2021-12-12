__all__ = (
    "ProcessingMessageConsumer",
)

import typing as t

import aio_pika

from asynchron.core.consumer import MessageConsumer


class ProcessingMessageConsumer(MessageConsumer[aio_pika.IncomingMessage]):
    def __init__(
            self,
            consumer: MessageConsumer[aio_pika.IncomingMessage],
            requeue_on_exception: bool = False,
            reject_on_redelivered: bool = False,
            ignore_processed: bool = False,
    ) -> None:
        self.__consumer = consumer
        self.__requeue_on_exception = requeue_on_exception
        self.__reject_on_redelivered = reject_on_redelivered
        self.__ignore_processed = ignore_processed

    async def consume(self, message: aio_pika.IncomingMessage) -> None:
        async with t.cast(t.AsyncContextManager[aio_pika.IncomingMessage], message.process(
                requeue=self.__requeue_on_exception,
                reject_on_redelivered=self.__reject_on_redelivered,
                ignore_processed=self.__ignore_processed,
        )):
            await self.__consumer.consume(message)
