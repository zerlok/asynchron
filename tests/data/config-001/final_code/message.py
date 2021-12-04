import typing

from pydantic import BaseModel, Field


class SensorTemperatureFahrenheitSensorReading(BaseModel):
    base_unit: typing.Optional[typing.Literal["CELSIUS", "FAHRENHEIT"]] = Field(
        alias="baseUnit",
    )
    sensor_id: typing.Optional[str] = Field(
        alias="sensorId",
    )
    temperature: typing.Optional[typing.Union[int, float]] = Field(
        alias="temperature",
    )
