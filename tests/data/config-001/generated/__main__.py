import asyncio
import typing

from asynchron.amqp.connector import AioPikaConnector
from asynchron.amqp.controller import AioPikaBasedAmqpController
from asynchron.core.amqp import AmqpServerBindings
from asynchron.core.application import ApplicationBuilder
from .consumer import (
    TemperatureReadingsConsumerFacade,
    bind_temperature_readings_consumers,
)
from .publisher import TemperatureReadingsPublisherProvider

builder = ApplicationBuilder(bind_temperature_readings_consumers)


@builder.env_name_based_server_factory("AMQP_BROKER_URL")
def create_server(value: typing.Optional[str]) -> AmqpServerBindings:
    return AmqpServerBindings(connection_url=value or "amqp://guest:guest@localhost:5672/")


@builder.runnable_factory
def create_controller(
        server: AmqpServerBindings,
) -> typing.AsyncContextManager[AioPikaBasedAmqpController]:
    return AioPikaConnector(
        bindings=server,
        consumer_factory=None,
        publisher_factory=None,
    )


@builder.consumer_facade_factory
def create_consumer_facade(
        server: AmqpServerBindings,
        controller: AioPikaBasedAmqpController,
) -> TemperatureReadingsConsumerFacade:
    publishers = TemperatureReadingsPublisherProvider(controller)

    return TemperatureReadingsConsumerFacade()


if __name__ == "__main__":
    asyncio.run(builder.build().run())
