# @formatter:off
from asynchron.amqp.controller import AioPikaBasedAmqpController
from asynchron.amqp.serializer.pydantic import PydanticMessageSerializer
from asynchron.core.amqp import AmqpPublisherBindings
from asynchron.core.publisher import MessagePublisher

from .message import (
    SensorReading,
)




class TemperatureReadingsPublisherFacade:
    """Temperature Readings"""

    def __init__(
            self,
            controller: AioPikaBasedAmqpController,
    ) -> None:
        self.__sensor_temperature_fahrenheit_publisher: MessagePublisher[SensorReading] = controller.bind_publisher(
            encoder=PydanticMessageSerializer(
                model=SensorReading,  # type: ignore[misc]
            ),
            bindings=AmqpPublisherBindings(
                exchange_name="events",
                routing_key="temperature.measured",
                is_mandatory=None,
                prefetch_count=None,
            ),
        )

    async def publish_sensor_temperature_fahrenheit(
            self,
            message: SensorReading,
    ) -> None:
        await self.__sensor_temperature_fahrenheit_publisher.publish(message)







# @formatter:on