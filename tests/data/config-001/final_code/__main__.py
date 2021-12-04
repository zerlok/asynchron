import asyncio

import aio_pika

from asyncapi.amqp.consumer.controller import ConsumersController
from asyncapi.amqp.consumer.factory import (
    ProcessingCallableDecodedMessageConsumerFactory,
    PydanticModelMessageConsumerFactory,
)
from .consumer import add_temperature_readings_consumers


async def main() -> None:
    connection = await aio_pika.connect_robust()  # type: aio_pika.Connection

    try:
        runner = ConsumersController(
            connection=connection,
            consumer_factory=ProcessingCallableDecodedMessageConsumerFactory(
                factory=PydanticModelMessageConsumerFactory(),
            ),
        )

        add_temperature_readings_consumers(runner, ...)

        runner.start()
        await runner.wait_for_termination()

    finally:
        await connection.close()  # type: ignore


if __name__ == "__main__":
    asyncio.run(main())
