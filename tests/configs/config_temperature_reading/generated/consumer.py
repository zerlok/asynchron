# @formatter:off
import abc

from asynchron.amqp.controller import AioPikaBasedAmqpController
from asynchron.amqp.serializer.pydantic import PydanticMessageSerializer
from asynchron.core.amqp import AmqpConsumerBindings
from asynchron.core.consumer import CallableMessageConsumer

from .message import (
    SensorReading,
)




class TemperatureReadingsConsumerFacade(metaclass=abc.ABCMeta):
    """Temperature Readings"""

    def __init__(
            self,
            controller: AioPikaBasedAmqpController,
    ) -> None:
        controller.bind_consumer(
            decoder=PydanticMessageSerializer(
                model=SensorReading,  # type: ignore[misc]
            ),
            consumer=CallableMessageConsumer(
                consumer=self.consume_temperature_measured,
            ),
            bindings=AmqpConsumerBindings(
                exchange_name="events",
                binding_keys=(
                    "temperature.measured",
                ),
                queue_name="measures",
                is_auto_delete_enabled=True,
                is_exclusive=None,
                is_durable=None,
                prefetch_count=100,
            ),
        )

    @abc.abstractmethod
    async def consume_temperature_measured(
            self,
            message: SensorReading,
    ) -> None:
        raise NotImplementedError







# @formatter:on
