import asyncio

from asynchron.amqp.controller import AioPikaBasedAmqpController
from asynchron.core.amqp import AmqpServerBindings
from generated.consumer import TemperatureReadingsConsumerFacade
from generated.message import SensorTemperatureFahrenheitSensorReading
from generated.publisher import TemperatureReadingsPublisherProvider
from generated.__main__ import builder


class TemperatureReadingsConsumerFacadeImpl(TemperatureReadingsConsumerFacade):
    def __init__(
            self,
            publishers: TemperatureReadingsPublisherProvider,
    ) -> None:
        self.__sensor_temperature_publisher = publishers.provide_sensor_temperature_fahrenheit_publisher()

    async def consume_sensor_temperature_fahrenheit(
            self,
            message: SensorTemperatureFahrenheitSensorReading,
    ) -> None:
        await self.__sensor_temperature_publisher.publish(SensorTemperatureFahrenheitSensorReading(
            baseUnit=message.base_unit,
            sensorId=message.sensor_id,
            temperature=message.temperature,
        ))


@builder.consumer_facade_factory
def create_consumer_facade(
        server: AmqpServerBindings,
        controller: AioPikaBasedAmqpController,
) -> TemperatureReadingsConsumerFacade:
    publishers = TemperatureReadingsPublisherProvider(controller)

    return TemperatureReadingsConsumerFacadeImpl(publishers)


if __name__ == "__main__":
    asyncio.run(builder.build().run())
