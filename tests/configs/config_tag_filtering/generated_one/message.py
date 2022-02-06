# @formatter:off
import pydantic
import typing




class ChannelsC001SubscribeMessagePayload(pydantic.BaseModel):
    bar: typing.Optional[str] = pydantic.Field(
        alias="bar",
    )


class ChannelsC002PublishMessagePayload(pydantic.BaseModel):
    bar: typing.Optional[str] = pydantic.Field(
        alias="bar",
    )


class ChannelsC003SubscribeMessagePayload(pydantic.BaseModel):
    bar: typing.Optional[str] = pydantic.Field(
        alias="bar",
    )








# @formatter:on
