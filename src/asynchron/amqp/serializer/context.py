__all__ = (
    "MessageContext",
    "MessageWithContext",
    "MessageWithContextDecoder",
    "MessageContextAssigningMessageEncoder",
)

import typing as t
from dataclasses import dataclass

import aio_pika

from asynchron.core.message import MessageDecoder, MessageEncoder

T = t.TypeVar("T")
T_co = t.TypeVar("T_co", covariant=True)
T_contra = t.TypeVar("T_contra", contravariant=True)


@dataclass(frozen=True)
class MessageContext:
    headers: t.Optional[t.Mapping[str, str]] = None
    correlation_id: t.Optional[str] = None
    reply_to: t.Optional[str] = None
    user_id: t.Optional[str] = None
    app_id: t.Optional[str] = None


@dataclass(frozen=True)
class MessageWithContext(t.Generic[T]):
    data: T
    headers: t.Mapping[str, str]
    correlation_id: t.Optional[str]
    reply_to: t.Optional[str]
    user_id: t.Optional[str]
    app_id: t.Optional[str]


class MessageWithContextDecoder(MessageDecoder[aio_pika.IncomingMessage, MessageWithContext[T_co]]):

    def __init__(
            self,
            decoder: MessageDecoder[aio_pika.IncomingMessage, T_co],
    ) -> None:
        self.__decoder = decoder

    def decode(self, message: aio_pika.IncomingMessage) -> MessageWithContext[T_co]:
        decoded_message = self.__decoder.decode(message)

        # TODO: remove type ignore, get typing stubs for aio-pika, maybe
        return MessageWithContext(
            data=decoded_message,
            headers=message.headers or {},  # type: ignore[misc]
            correlation_id=message.correlation_id,  # type: ignore[misc]
            reply_to=message.reply_to,  # type: ignore[misc]
            user_id=message.user_id,  # type: ignore[misc]
            app_id=message.app_id,  # type: ignore[misc]
        )


class MessageContextAssigningMessageEncoder(MessageEncoder[T_contra, aio_pika.Message]):

    def __init__(
            self,
            encoder: MessageEncoder[T_contra, aio_pika.Message],
            context_provider: t.Optional[t.Callable[[T_contra], t.Optional[MessageContext]]] = None,
    ) -> None:
        self.__encoder = encoder
        self.__context_provider = context_provider or self.__provide_empty_context

    def encode(self, message: T_contra) -> aio_pika.Message:
        context = self.__context_provider(message)
        encoded_message = self.__encoder.encode(message)

        if context is not None:
            if context.headers is not None:
                encoded_message.headers = context.headers

            if context.correlation_id is not None:
                encoded_message.correlation_id = context.correlation_id

            if context.reply_to is not None:
                encoded_message.reply_to = context.reply_to

            if context.user_id is not None:
                encoded_message.user_id = context.user_id

            if context.app_id is not None:
                encoded_message.app_id = context.app_id

        return encoded_message

    @staticmethod
    def __provide_empty_context(message: T_contra) -> None:
        return None
