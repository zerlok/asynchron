# @formatter:off
import typing

import pydantic




class SensorReading(pydantic.BaseModel):
    base_unit: typing.Optional[typing.Literal['CELSIUS', 'FAHRENHEIT']] = pydantic.Field(
        alias="baseUnit",
    )
    sensor_id: typing.Optional[str] = pydantic.Field(
        alias="sensorId",
    )
    temperature: typing.Optional[typing.Union[int, float]] = pydantic.Field(
        alias="temperature",
    )








# @formatter:on
