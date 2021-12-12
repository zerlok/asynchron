__all__ = (
    "EncodedWithContextMessagePublisherFactory",
)

import typing as t

import aio_pika

from asynchron.amqp.serializer.context import MessageContext, MessageContextAssigningMessageEncoder
from asynchron.core.message import MessageEncoder
from asynchron.core.publisher import EncodedMessagePublisher, MessagePublisher, MessagePublisherFactory

T = t.TypeVar("T")
T_contra = t.TypeVar("T_contra", contravariant=True)
T_co = t.TypeVar("T_co", covariant=True)


class EncodedWithContextMessagePublisherFactory(
    MessagePublisherFactory[t.Tuple[MessageEncoder[T, aio_pika.Message], MessagePublisher[aio_pika.Message]], T],
):
    def __init__(
            self,
            context_provider: t.Optional[t.Callable[[T], t.Optional[MessageContext]]] = None,
    ) -> None:
        self.__context_provider = context_provider

    def create_publisher(
            self,
            settings: t.Tuple[MessageEncoder[T, aio_pika.Message], MessagePublisher[aio_pika.Message]],
    ) -> MessagePublisher[T]:
        encoder, publisher = settings

        return EncodedMessagePublisher(
            encoder=MessageContextAssigningMessageEncoder[T](
                encoder=encoder,
                context_provider=self.__context_provider,
            ),
            publisher=publisher,
        )
