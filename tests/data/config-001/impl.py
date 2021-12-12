from .generated.consumer import TemperatureReadingsConsumerFacade
from .generated.message import SensorTemperatureFahrenheitSensorReading
from .generated.publisher import TemperatureReadingsPublisherProvider


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
