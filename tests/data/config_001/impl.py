import asyncio
import typing as t

from asynchron.amqp.connector import AmqpConnector
from asynchron.amqp.controller import AioPikaBasedAmqpController
from asynchron.core.amqp import AmqpServerBindings
from asynchron.core.application import ApplicationBuilder
from asynchron.core.controller import Runnable
from .generated.consumer import TemperatureReadingsConsumerFacade
from .generated.message import SensorReading
from .generated.publisher import TemperatureReadingsPublisherFacade

builder = ApplicationBuilder()


class TemperatureReadingsConsumerFacadeImpl(TemperatureReadingsConsumerFacade):
    def __init__(self, controller: AioPikaBasedAmqpController, publishers: TemperatureReadingsPublisherFacade) -> None:
        super().__init__(controller)
        self.__publishers = publishers

    async def consume_sensor_temperature_fahrenheit(
            self,
            message: SensorReading,
    ) -> None:
        await self.__publishers.publish_sensor_temperature_fahrenheit(SensorReading(
            baseUnit=message.base_unit,
            sensorId=message.sensor_id,
            temperature=message.temperature,
        ))


@builder.runnable_factory
async def startup() -> t.AsyncIterator[Runnable]:
    async with AmqpConnector(
            bindings=AmqpServerBindings(connection_url="..."),
    ) as connector:
        controller = AioPikaBasedAmqpController(connector)

        publishers = TemperatureReadingsPublisherFacade(controller)
        consumers = TemperatureReadingsConsumerFacadeImpl(controller, publishers)

        yield controller


if __name__ == "__main__":
    app = builder.build()
    asyncio.run(app.run())
