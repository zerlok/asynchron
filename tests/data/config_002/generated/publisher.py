# @formatter:off
from asynchron.amqp.controller import AioPikaBasedAmqpController
from asynchron.amqp.serializer.pydantic import PydanticMessageSerializer
from asynchron.core.amqp import AmqpPublisherBindings
from asynchron.core.publisher import MessagePublisher

from .message import (
    MainFoo,
)




class ComplexSchemaObjectsPublisherFacade:
    """This configuration contains complex schema objects to test pydantic model codegen"""

    def __init__(
            self,
            controller: AioPikaBasedAmqpController,
    ) -> None:
        self.__foo_publisher: MessagePublisher[MainFoo] = controller.bind_publisher(
            encoder=PydanticMessageSerializer(
                model=MainFoo,  # type: ignore[misc]
            ),
            bindings=AmqpPublisherBindings(
                exchange_name="",
                routing_key="foo",
                is_mandatory=None,
                prefetch_count=None,
            ),
        )

    async def publish_foo(
            self,
            message: MainFoo,
    ) -> None:
        await self.__foo_publisher.publish(message)







# @formatter:on
