# @formatter:off
import pydantic
import typing




class ChannelsC001SubscribeMessagePayload(pydantic.BaseModel):
    bar: typing.Optional[str] = pydantic.Field(
        alias="bar",
    )


class ChannelsC002SubscribeMessagePayload(pydantic.BaseModel):
    bar: typing.Optional[str] = pydantic.Field(
        alias="bar",
    )








# @formatter:on
