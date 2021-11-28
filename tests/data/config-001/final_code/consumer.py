import abc

from asyncapi.amqp.base import ConsumptionContext
from asyncapi.amqp.consumer.callable import CallableMessageConsumer
from asyncapi.amqp.consumer.decoded import DecodedMessageConsumer
from asyncapi.amqp.consumer.processing import ProcessingMessageConsumer
from asyncapi.amqp.consumer.runner import ConsumersRunner
from asyncapi.amqp.decoder.pydantic import PydanticModelMessageDecoder
from .message import SensorReading


class TemperatureReadingsConsumerManager(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def consume_sensor_reading_message(self, message: SensorReading, context: ConsumptionContext) -> None:
        raise NotImplementedError


def add_temperature_readings_consumers(runner: ConsumersRunner, manager: TemperatureReadingsConsumerManager) -> None:
    runner.add_consumer(
        exchange_name="events",
        binding_keys=("temperature.measured",),
        consumer=ProcessingMessageConsumer(
            DecodedMessageConsumer(CallableMessageConsumer(manager.consume_sensor_reading_message),
                                   PydanticModelMessageDecoder(SensorReading), )),
        queue_name="measures",
        is_auto_delete_enabled=True,
        is_exclusive=None,
        is_durable=None,
        prefetch_count=None,
    )
