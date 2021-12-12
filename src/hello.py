# generated code
import abc
import asyncio
import typing as t

import aio_pika

from asynchron.amqp.connector import AioPikaConnector
from asynchron.amqp.controller import AioPikaBasedAmqpController
from asynchron.core.amqp import AmqpConsumerBindings, AmqpPublisherBindings, AmqpServerBindings
from asynchron.core.application import ApplicationBuilder
from asynchron.core.consumer import CallableMessageConsumer
from asynchron.core.message import MessageSerializer
from asynchron.core.publisher import MessagePublisher


class StringSerializer(MessageSerializer[aio_pika.Message, str]):

    def decode(self, message: aio_pika.Message) -> str:
        return message.body.decode(message.content_encoding)

    def encode(self, message: str) -> aio_pika.Message:
        return aio_pika.Message(body=message.encode("utf-8"), content_encoding="utf-8")


class GreetingsPublisherProvider:
    # generated provider implementation
    def __init__(self, controller: AioPikaBasedAmqpController) -> None:
        self.__controller = controller

    def provide_hello_publisher(self) -> MessagePublisher[str]:
        return self.__controller.bind_publisher(
            encoder=StringSerializer(),
            bindings=AmqpPublisherBindings(
                exchange_name="events",
                routing_key="greeting.performed",
                prefetch_count=1,
            ),
        )


class GreetingsConsumerFacade(metaclass=abc.ABCMeta):
    # generated facade interface

    @abc.abstractmethod
    async def consume_greeting(self, message: str) -> None:
        raise NotImplementedError


def setup_consumers(
        server: AmqpServerBindings,
        controller: AioPikaBasedAmqpController,
        facade: GreetingsConsumerFacade,
) -> None:
    # generate consumer attaching code
    controller.bind_consumer(
        decoder=StringSerializer(),
        consumer=CallableMessageConsumer(facade.consume_greeting),
        bindings=AmqpConsumerBindings(
            exchange_name="events",
            binding_keys=("greeting.asked",),
            queue_name="greetings",
            is_auto_delete_enabled=True,
            prefetch_count=1,
        ),
    )


builder = ApplicationBuilder(setup_consumers)


@builder.env_name_based_server_factory("AMQP_BROKER_URL")
def create_server(name: t.Optional[str]) -> AmqpServerBindings:
    if name is None:
        raise ValueError()

    return AmqpServerBindings(connection_url=name)


@builder.runnable_factory
def create_controller(server: AmqpServerBindings) -> t.AsyncContextManager[AioPikaBasedAmqpController]:
    return AioPikaConnector(
        bindings=server,
        # consumer_factory=ProcessingCallableDecodedMessageConsumerFactory(),
    )


# user code (implementations)

class GreetingsConsumerFacadeImpl(GreetingsConsumerFacade):
    def __init__(self, publishers: GreetingsPublisherProvider) -> None:
        self.__greet_publisher = publishers.provide_hello_publisher()

    async def consume_greeting(self, message: str) -> None:
        await self.__greet_publisher.publish(f"Hello, {message}!")


@builder.consumer_facade_factory
def setup(
        server: AmqpServerBindings,
        controller: AioPikaBasedAmqpController,
) -> GreetingsConsumerFacade:
    return GreetingsConsumerFacadeImpl(GreetingsPublisherProvider(controller))


if __name__ == "__main__":
    asyncio.run(builder.build().run())
