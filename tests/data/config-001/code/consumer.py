import abc
import asyncio

import aio_pika

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
        exchange_name="hello",
        binding_keys=("worlkd",),
        consumer=ProcessingMessageConsumer(
            DecodedMessageConsumer(CallableMessageConsumer(manager.consume_sensor_reading_message),
                                   PydanticModelMessageDecoder(SensorReading), )),
    )


async def main():
    connection = await aio_pika.connect_robust()

    try:
        runner = ConsumersRunner(connection)

        runner.start()
        await runner.wait_for_termination()

    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
