__all__ = (
    "ProcessingCallableDecodedMessageConsumerFactory",
)

import typing as t

import aio_pika

from asynchron.amqp.consumer.processing import ProcessingMessageConsumer
from asynchron.core.consumer import (
    MessageConsumer,
    MessageConsumerFactory,
)

T = t.TypeVar("T")
T_contra = t.TypeVar("T_contra", contravariant=True)


class ProcessingCallableDecodedMessageConsumerFactory(
    MessageConsumerFactory[MessageConsumer[aio_pika.IncomingMessage], aio_pika.IncomingMessage],
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
            settings: MessageConsumer[aio_pika.IncomingMessage],
    ) -> MessageConsumer[aio_pika.IncomingMessage]:
        # callable_consumer_wrapper = CallableMessageConsumer(consumer=callable_consumer, )
        # message_with_context_decoder = MessageWithContextDecoder(decoder=decoder, )
        #
        # # FIXME: cast fixes mypy error
        # #  note: Revealed type is "asynchron.amqp.decoder.context.MessageWithContextDecoder[T`1]"
        # #  error: Cannot infer type argument 1 of "DecodedMessageConsumer"  [misc]
        # # reveal_type(message_with_context_decoder)
        # consumer = DecodedMessageConsumer(consumer=callable_consumer_wrapper,
        #                                   decoder=t.cast(MessageDecoder[aio_pika.IncomingMessage, T],
        #                                                  message_with_context_decoder), )

        return ProcessingMessageConsumer(
            consumer=settings,
            requeue_on_exception=self.__requeue_on_exception,
            reject_on_redelivered=self.__reject_on_redelivered,
            ignore_processed=self.__ignore_processed,
        )
