import typing as t

from pydantic import BaseModel, Field


class SensorReading(BaseModel):
    sensor_id: str = Field(
        alias="sensorId",
        description="""""",
    )

    temperature: int = Field(
        alias="temperature",
        description="""""",
    )

    base_unit: t.Literal["CELSIUS", "FAHRENHEIT"] = Field(
        alias="base_unit",
        description="""""",
    )
