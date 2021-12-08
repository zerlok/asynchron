__all__ = (
    "PydanticModelMessageEncoder",
    "PydanticModelMessageDecoder",
)

import pickle
import typing as t

import aio_pika
from pydantic import BaseModel, Protocol

from asynchron.amqp.base import ConsumptionContext, MessageDecoder, MessageEncoder
from asynchron.strict_typing import raise_not_exhaustive

T_contra = t.TypeVar("T_contra", bound=BaseModel, contravariant=True)
T_model = t.TypeVar("T_model", bound=BaseModel)


class PydanticModelMessageEncoder(MessageEncoder[T_contra]):

    def __init__(
            self,
            model: t.Type[T_contra],
            protocol: Protocol = Protocol.json,
    ) -> None:
        self.__model = model
        self.__protocol = protocol

    def encode(self, message: T_contra) -> aio_pika.Message:
        if self.__protocol is Protocol.json:
            return aio_pika.Message(
                body=message.json().encode("utf-8"),
                content_type="application/json",
                content_encoding="utf-8",
            )

        elif self.__protocol is Protocol.pickle:
            return aio_pika.Message(
                body=pickle.dumps(message),
                content_type="python/pickle",
            )

        else:
            raise_not_exhaustive(self.__protocol)


class PydanticModelMessageDecoder(MessageDecoder[T_model]):

    def __init__(
            self,
            model: t.Type[T_model],
            protocol: Protocol = Protocol.json,
    ) -> None:
        self.__model = model
        self.__protocol = protocol

    def decode(self, message: aio_pika.IncomingMessage, context: ConsumptionContext) -> T_model:
        return self.__model.parse_raw(
            b=message.body,
            content_type=message.content_type,
            encoding=message.content_encoding,
            proto=self.__protocol,
            allow_pickle=self.__protocol is Protocol.pickle,
        )
