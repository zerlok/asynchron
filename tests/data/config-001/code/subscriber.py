import abc


class SensorReadingPublisher(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def publish_sensor_reading_message(self, message: "SensorReading") -> None:
        raise NotImplementedError
