import asyncio

import aio_pika

from asyncapi.amqp.consumer.runner import ConsumersRunner
from .consumer import add_temperature_readings_consumers


async def main() -> None:
    connection = await aio_pika.connect_robust()  # type: aio_pika.Connection

    try:
        runner = ConsumersRunner(connection)

        add_temperature_readings_consumers(runner, ...)

        runner.start()
        await runner.wait_for_termination()

    finally:
        await connection.close()  # type: ignore


if __name__ == "__main__":
    asyncio.run(main())
