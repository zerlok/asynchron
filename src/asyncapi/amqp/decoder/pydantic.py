__all__ = (
    "PydanticModelMessageDecoder",
)

import typing as t

import aio_pika
from pydantic import BaseModel, Protocol

from asyncapi.amqp.base import ConsumptionContext, MessageDecoder

T_model = t.TypeVar("T_model", bound=BaseModel)


class PydanticModelMessageDecoder(MessageDecoder[T_model]):

    def __init__(
            self,
            model: t.Type[T_model],
            protocol_getter: t.Optional[t.Callable[[aio_pika.IncomingMessage], t.Optional[Protocol]]] = None,
    ) -> None:
        self.__model = model
        self.__protocol_getter = protocol_getter or self.__get_none_protocol

    def decode(self, message: aio_pika.IncomingMessage, context: ConsumptionContext) -> T_model:
        return self.__model.parse_raw(
            b=message.body,
            content_type=message.content_type,
            encoding=message.content_encoding,
            proto=self.__protocol_getter(message),
        )

    def __get_none_protocol(self, _: aio_pika.IncomingMessage) -> t.Optional[Protocol]:
        return None
