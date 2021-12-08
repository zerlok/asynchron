import asyncio

import aio_pika

from asynchron.amqp.consumer.controller import ConsumersController
from asynchron.amqp.consumer.factory import (
    ProcessingCallableDecodedMessageConsumerFactory,
)
from .consumer import add_temperature_readings_consumers


async def main() -> None:
    connection = await aio_pika.connect_robust()  # type: aio_pika.Connection

    try:
        runner = ConsumersController(
            connection=connection,
            consumer_factory=ProcessingCallableDecodedMessageConsumerFactory(),
        )

        add_temperature_readings_consumers(runner, ...)

        runner.start()
        await runner.wait_for_termination()

    finally:
        await connection.close()  # type: ignore


if __name__ == "__main__":
    asyncio.run(main())
