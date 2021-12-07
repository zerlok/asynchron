import aio_pika

from asyncapi.amqp.base import MessagePublisher
from asyncapi.amqp.decoder.pydantic import PydanticModelMessageEncoder
from asyncapi.amqp.publisher.controller import PublishersController
from asyncapi.amqp.publisher.factory import ExchangeBasedEncodedWithContextMessagePublisherFactory
from .message import (
    SensorTemperatureFahrenheitSensorReading,
)


class TemperatureReadingsPublisherFactory:
    """Temperature Readings"""

    def __init__(
            self,
            connection: aio_pika.Connection,
    ) -> None:
        self.__publishers = PublishersController(
            connection=connection,
            publisher_factory=ExchangeBasedEncodedWithContextMessagePublisherFactory(),
        )

    async def publish_sensor_temperature_fahrenheit(
            self,
    ) -> MessagePublisher[SensorTemperatureFahrenheitSensorReading]:
        return await self.__publishers.create_publisher(
            exchange_name="events",
            exchange_type="direct",
            routing_key="temperature.measured",
            publisher=PydanticModelMessageEncoder(
                model=SensorTemperatureFahrenheitSensorReading,
            ),
            is_auto_delete_enabled=None,
            is_durable=None,
            is_mandatory=None,
            prefetch_count=None,
        )
