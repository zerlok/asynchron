__all__ = (
    "PydanticMessageSerializer",
)

import pickle
import typing as t

import aio_pika
from pydantic import BaseModel, Protocol

from asynchron.core.message import MessageSerializer
from asynchron.strict_typing import raise_not_exhaustive

T_model = t.TypeVar("T_model", bound=BaseModel)


class PydanticMessageSerializer(t.Generic[T_model], MessageSerializer[aio_pika.Message, T_model]):

    def __init__(
            self,
            model: t.Type[T_model],
            protocol: Protocol = Protocol.json,
    ) -> None:
        self.__model = model
        self.__protocol = protocol

    def decode(self, message: aio_pika.Message) -> T_model:
        return self.__model.parse_raw(
            b=message.body,
            content_type=message.content_type or "",
            encoding=message.content_encoding or "utf8",
            proto=self.__protocol,
            allow_pickle=self.__protocol is Protocol.pickle,
        )

    def encode(self, message: T_model) -> aio_pika.Message:
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
