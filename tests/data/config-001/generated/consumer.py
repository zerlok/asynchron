# @formatter:off
import abc

from asynchron.amqp.controller import AioPikaBasedAmqpController
from asynchron.amqp.serializer.pydantic import PydanticMessageSerializer
from asynchron.core.amqp import AmqpConsumerBindings, AmqpServerBindings
from asynchron.core.consumer import CallableMessageConsumer

from .message import (
    SensorTemperatureFahrenheitMessage,
)




class TemperatureReadingsConsumerFacade(metaclass=abc.ABCMeta):
    """Temperature Readings"""

    def __init__(
            self,
            controller: AioPikaBasedAmqpController,
    ) -> None:
        controller.bind_consumer(
            decoder=PydanticMessageSerializer(
                model=SensorTemperatureFahrenheitMessage,  # type: ignore[misc]
            ),
            consumer=CallableMessageConsumer(
                consumer=self.consume_sensor_temperature_fahrenheit,
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

    @abc.abstractmethod
    async def consume_sensor_temperature_fahrenheit(
            self,
            message: SensorTemperatureFahrenheitMessage,
    ) -> None:
        raise NotImplementedError







# @formatter:on
