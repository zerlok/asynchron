__all__ = (
    "PydanticModelMessageConsumerFactory",
    "ProcessingCallableDecodedMessageConsumerFactory",
)

import typing as t

import aio_pika
from pydantic import BaseModel, Protocol

from asyncapi.amqp.base import (
    MessageConsumer,
    MessageConsumerFactory,
)
from asyncapi.amqp.consumer.callable import CallableInvokingMessageConsumer, CallableMessageConsumer
from asyncapi.amqp.consumer.decoded import DecodedMessageConsumer
from asyncapi.amqp.consumer.processing import ProcessingMessageConsumer
from asyncapi.amqp.decoder.pydantic import PydanticModelMessageDecoder

T = t.TypeVar("T")
T_model = t.TypeVar("T_model", bound=BaseModel)


class PydanticModelMessageConsumerFactory(
    MessageConsumerFactory[t.Tuple[t.Type[T_model], MessageConsumer[T_model]]],
):
    def __init__(
            self,
            protocol: Protocol = Protocol.json,
    ) -> None:
        self.__protocol = protocol

    def create_consumer(
            self,
            consumer: t.Tuple[t.Type[T_model], MessageConsumer[T_model]],
    ) -> MessageConsumer[aio_pika.IncomingMessage]:
        model, model_consumer = consumer

        return DecodedMessageConsumer(
            consumer=model_consumer,
            decoder=PydanticModelMessageDecoder(
                model=model,
                protocol=self.__protocol,
            ),
        )


class ProcessingCallableDecodedMessageConsumerFactory(
    MessageConsumerFactory[t.Tuple[t.Type[T_model], CallableMessageConsumer[T_model]]],
):
    def __init__(
            self,
            factory: MessageConsumerFactory[t.Tuple[t.Type[T_model], MessageConsumer[T_model]]],
            requeue_on_exception: bool = False,
            reject_on_redelivered: bool = False,
            ignore_processed: bool = False,
    ) -> None:
        self.__factory = factory
        self.__requeue_on_exception = requeue_on_exception
        self.__reject_on_redelivered = reject_on_redelivered
        self.__ignore_processed = ignore_processed

    def create_consumer(
            self,
            consumer: t.Tuple[t.Type[T_model], CallableMessageConsumer[T_model]],
    ) -> MessageConsumer[aio_pika.IncomingMessage]:
        model, callable_consumer = consumer

        return ProcessingMessageConsumer(
            consumer=self.__factory.create_consumer((
                model,
                CallableInvokingMessageConsumer(callable_consumer),
            )),
            requeue_on_exception=self.__requeue_on_exception,
            reject_on_redelivered=self.__reject_on_redelivered,
            ignore_processed=self.__ignore_processed,
        )
