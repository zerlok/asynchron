import abc

from asynchron.amqp.controller import AioPikaBasedAmqpController
from asynchron.amqp.serializer.pydantic import PydanticMessageSerializer
from asynchron.core.amqp import AmqpConsumerBindings, AmqpServerBindings
from asynchron.core.consumer import CallableMessageConsumer
from .message import (
    SensorTemperatureFahrenheitSensorReading,
)


class TemperatureReadingsConsumerFacade(metaclass=abc.ABCMeta):
    """Temperature Readings"""

    @abc.abstractmethod
    async def consume_sensor_temperature_fahrenheit(
            self,
            message: SensorTemperatureFahrenheitSensorReading,
    ) -> None:
        raise NotImplementedError


def bind_temperature_readings_consumers(
        server: AmqpServerBindings,
        consumers: AioPikaBasedAmqpController,
        facade: TemperatureReadingsConsumerFacade,
) -> None:
    consumers.bind_consumer(
        decoder=PydanticMessageSerializer(
            model=SensorTemperatureFahrenheitSensorReading,
        ),
        consumer=CallableMessageConsumer(
            consumer=facade.consume_sensor_temperature_fahrenheit,
        ),
        bindings=AmqpConsumerBindings(
            exchange_name="events",
            binding_keys=(
                "temperature.measured",
            ),
            queue_name="measures",
            is_auto_delete_enabled=None,
            is_exclusive=None,
            is_durable=None,
            prefetch_count=None,
        ),
    )
