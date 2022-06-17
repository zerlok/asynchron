__all__ = (
    "ExchangeMessagePublisher",
)

import typing as t

from aio_pika.abc import AbstractExchange, AbstractMessage
from aio_pika.types import TimeoutType

from asynchron.core.publisher import MessagePublisher


class PublishFunc(t.Protocol):
    async def __call__(
            self,
            message: AbstractMessage,
            routing_key: str,
            *,
            mandatory: bool = True,
            immediate: bool = False,
            timeout: t.Optional[TimeoutType] = None,
    ) -> None: ...


class ExchangeMessagePublisher(MessagePublisher[AbstractMessage]):

    def __init__(
            self,
            routing_key: str,
            is_mandatory: bool,
            exchange: t.Optional[AbstractExchange] = None,
    ) -> None:
        self.__publish = self.__raise_error
        self.__routing_key = routing_key
        self.__is_mandatory = is_mandatory

        if exchange is not None:
            self.attach(exchange)

    async def publish(self, message: AbstractMessage) -> None:
        await self.__publish(
            message=message,
            routing_key=self.__routing_key,
            mandatory=self.__is_mandatory,
        )

    def attach(self, exchange: AbstractExchange) -> None:
        # FIXME: fix typing in aio_pika lib (t.Optional[TimeoutType]).
        self.__publish = t.cast(PublishFunc, exchange.publish)

    async def __raise_error(
            self,
            message: AbstractMessage,
            routing_key: str,
            *,
            mandatory: bool = True,
            immediate: bool = False,
            timeout: t.Optional[TimeoutType] = None,
    ) -> None:
        raise RuntimeError()
