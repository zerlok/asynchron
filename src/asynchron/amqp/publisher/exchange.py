__all__ = (
    "ExchangeMessagePublisher",
)

import aio_pika

from asynchron.amqp.base import MessagePublisher


class ExchangeMessagePublisher(MessagePublisher[aio_pika.Message]):
    def __init__(
            self,
            exchange: aio_pika.Exchange,
            routing_key: str,
            is_mandatory: bool,
    ) -> None:
        self.__exchange = exchange
        self.__routing_key = routing_key
        self.__is_mandatory = is_mandatory

    async def publish(self, message: aio_pika.Message) -> None:
        await self.__exchange.publish(
            message=message,
            routing_key=self.__routing_key,
            mandatory=self.__is_mandatory,
        )  # type: ignore[misc]
