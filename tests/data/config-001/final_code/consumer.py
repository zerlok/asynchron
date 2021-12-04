import abc
import typing

from pydantic import BaseModel

from asyncapi.amqp.base import ConsumptionContext
from asyncapi.amqp.consumer.callable import CallableMessageConsumer
from asyncapi.amqp.consumer.controller import ConsumersController
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
        runner: ConsumersController[typing.Tuple[BaseModel, CallableMessageConsumer[BaseModel]]],
        manager: TemperatureReadings,
) -> None:
    runner.add_consumer(
        exchange_name="events",
        binding_keys=(
            "temperature.measured",
        ),
        consumer=(
            SensorTemperatureFahrenheitSensorReading,
            manager.consume_sensor_temperature_fahrenheit,
        ),
        queue_name="measures",
        is_auto_delete_enabled=None,
        is_exclusive=None,
        is_durable=None,
        prefetch_count=None,
    )
