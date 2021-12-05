import typing

import aio_pika
from pydantic import BaseModel

from asyncapi.amqp.base import MessagePublisher
from asyncapi.amqp.publisher.controller import PublishersController
from asyncapi.amqp.publisher.factory import (
    ExchangeBasedEncodedMessagePublisherFactory,
    PydanticModelMessagePublisherFactory,
)
from .message import (
    SensorTemperatureFahrenheitSensorReading,
)

T_model = typing.TypeVar("T_model", bound=BaseModel)


class TemperatureReadingsPublisherProvider:
    """Temperature Readings"""

    def __init__(
            self,
            connection: aio_pika.Connection,
    ) -> None:
        self.__publishers = PublishersController(
            connection=connection,
            publisher_factory=ExchangeBasedEncodedMessagePublisherFactory(
                factory=PydanticModelMessagePublisherFactory(),
            ),
        )

    async def provide_sensor_temperature_fahrenheit(
            self,
    ) -> MessagePublisher[SensorTemperatureFahrenheitSensorReading]:
        return await self.__publishers.create_publisher(
            exchange_name="events",
            exchange_type="direct",
            routing_key="temperature.measured",
            publisher=SensorTemperatureFahrenheitSensorReading,
            is_auto_delete_enabled=None,
            is_durable=None,
            is_mandatory=None,
            prefetch_count=None,
        )
