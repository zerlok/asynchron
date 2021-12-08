import abc
import typing

from pydantic import BaseModel

from asynchron.amqp.base import ConsumptionContext, MessageDecoder
from asynchron.amqp.consumer.callable import CallableMessageConsumer
from asynchron.amqp.consumer.controller import ConsumersController
from asynchron.amqp.decoder.pydantic import PydanticModelMessageDecoder
from .message import (
    SensorTemperatureFahrenheitSensorReading,
)


class TemperatureReadings(metaclass=abc.ABCMeta):
    """Temperature Readings"""

    @abc.abstractmethod
    async def consume_sensor_temperature_fahrenheit(
            self,
            message: SensorTemperatureFahrenheitSensorReading,
            context: ConsumptionContext,
    ) -> None:
        raise NotImplementedError


def add_temperature_readings_consumers(
        consumers: ConsumersController[typing.Tuple[MessageDecoder[BaseModel], CallableMessageConsumer[BaseModel]]],
        manager: TemperatureReadings,
) -> None:
    consumers.add_consumer(
        exchange_name="events",
        binding_keys=(
            "temperature.measured",
        ),
        consumer=(
            PydanticModelMessageDecoder(
                model=SensorTemperatureFahrenheitSensorReading,
            ),
            manager.consume_sensor_temperature_fahrenheit,
        ),
        queue_name="measures",
        is_auto_delete_enabled=None,
        is_exclusive=None,
        is_durable=None,
        prefetch_count=None,
    )
