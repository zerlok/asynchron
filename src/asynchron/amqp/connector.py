__all__ = (
    "AioPikaConnector",
)

import typing as t
from types import TracebackType

import aio_pika

from asynchron.amqp.controller import AioPikaBasedAmqpController
from asynchron.core.amqp import AmqpServerBindings
from asynchron.core.consumer import MessageConsumer, MessageConsumerFactory
from asynchron.core.publisher import MessagePublisher, MessagePublisherFactory

T = t.TypeVar("T")


class AioPikaConnector(t.AsyncContextManager[AioPikaBasedAmqpController]):
    def __init__(
            self,
            bindings: AmqpServerBindings,
            consumer_factory: t.Optional[MessageConsumerFactory[
                MessageConsumer[aio_pika.IncomingMessage],
                aio_pika.IncomingMessage,
            ]] = None,
            publisher_factory: t.Optional[MessagePublisherFactory[
                MessagePublisher[aio_pika.Message],
                aio_pika.Message
            ]] = None,
    ) -> None:
        self.__bindings = bindings
        self.__connection: t.Optional[aio_pika.Connection] = None
        self.__consumer_factory = consumer_factory
        self.__publisher_factory = publisher_factory

    async def __aenter__(self) -> AioPikaBasedAmqpController:
        if self.__connection is not None:
            raise RuntimeError()

        connection = await aio_pika.connect_robust(
            self.__bindings.connection_url)  # type: aio_pika.Connection

        self.__connection = connection

        return AioPikaBasedAmqpController(
            connection=connection,
            consumer_factory=self.__consumer_factory,
            publisher_factory=self.__publisher_factory,
        )

    async def __aexit__(
            self,
            __exc_type: t.Optional[t.Type[BaseException]],
            __exc_value: t.Optional[BaseException],
            __traceback: t.Optional[TracebackType],
    ) -> t.Optional[bool]:
        if self.__connection is not None:
            await self.__connection.close(__exc_type)  # type: ignore

        return None
