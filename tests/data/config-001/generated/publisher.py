from asynchron.amqp.controller import AioPikaBasedAmqpController
from asynchron.amqp.serializer.pydantic import PydanticMessageSerializer
from asynchron.core.amqp import AmqpPublisherBindings
from asynchron.core.publisher import MessagePublisher
from .message import (
    SensorTemperatureFahrenheitSensorReading,
)


class TemperatureReadingsPublisherProvider:
    """Temperature Readings"""

    def __init__(
            self,
            controller: AioPikaBasedAmqpController,
    ) -> None:
        self.__controller = controller

    def provide_sensor_temperature_fahrenheit_publisher(
            self,
    ) -> MessagePublisher[SensorTemperatureFahrenheitSensorReading]:
        return self.__controller.bind_publisher(
            encoder=PydanticMessageSerializer(
                model=SensorTemperatureFahrenheitSensorReading,
            ),
            bindings=AmqpPublisherBindings(
                exchange_name="events",
                routing_key="temperature.measured",
                is_mandatory=None,
                prefetch_count=None,
            ),
        )
