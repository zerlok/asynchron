__all__ = (
    "ProcessingCallableDecodedMessageConsumerFactory",
)

import typing as t

import aio_pika

from asyncapi.amqp.base import (
    MessageConsumer,
    MessageConsumerFactory, MessageDecoder,
)
from asyncapi.amqp.consumer.callable import CallableInvokingMessageConsumer, CallableMessageConsumer
from asyncapi.amqp.consumer.decoded import DecodedMessageConsumer
from asyncapi.amqp.consumer.processing import ProcessingMessageConsumer
from asyncapi.amqp.decoder.context import MessageWithContextDecoder

T_contra = t.TypeVar("T_contra", contravariant=True)


class ProcessingCallableDecodedMessageConsumerFactory(
    MessageConsumerFactory[
        t.Tuple[MessageDecoder[T_contra], CallableMessageConsumer[T_contra]],
        aio_pika.IncomingMessage,
    ],
):
    def __init__(
            self,
            requeue_on_exception: bool = False,
            reject_on_redelivered: bool = False,
            ignore_processed: bool = False,
    ) -> None:
        self.__requeue_on_exception = requeue_on_exception
        self.__reject_on_redelivered = reject_on_redelivered
        self.__ignore_processed = ignore_processed

    def create_consumer(
            self,
            settings: t.Tuple[MessageDecoder[T_contra], CallableMessageConsumer[T_contra]],
    ) -> MessageConsumer[aio_pika.IncomingMessage]:
        decoder, callable_consumer = settings

        callable_consumer_wrapper = CallableInvokingMessageConsumer(consumer=callable_consumer, )
        message_with_context_decoder = MessageWithContextDecoder(decoder=decoder, )

        # FIXME: cast fixes mypy error
        #  note: Revealed type is "asyncapi.amqp.decoder.context.MessageWithContextDecoder[T`1]"
        #  error: Cannot infer type argument 1 of "DecodedMessageConsumer"  [misc]
        # reveal_type(message_with_context_decoder)
        consumer = DecodedMessageConsumer(consumer=callable_consumer_wrapper,
                                          decoder=t.cast(MessageDecoder[T_contra], message_with_context_decoder), )

        return ProcessingMessageConsumer(
            consumer=consumer,
            requeue_on_exception=self.__requeue_on_exception,
            reject_on_redelivered=self.__reject_on_redelivered,
            ignore_processed=self.__ignore_processed,
        )
