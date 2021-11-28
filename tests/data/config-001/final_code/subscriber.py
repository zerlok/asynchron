import abc

from .message import SensorReading


class SensorReadingPublisher(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def publish_sensor_reading_message(self, message: SensorReading) -> None:
        raise NotImplementedError
