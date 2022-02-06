# @formatter:off
from asynchron.amqp.controller import AioPikaBasedAmqpController
from asynchron.amqp.serializer.pydantic import PydanticMessageSerializer
from asynchron.core.amqp import AmqpPublisherBindings
from asynchron.core.publisher import MessagePublisher

from .message import (
    ChannelsC001SubscribeMessagePayload,
    ChannelsC003SubscribeMessagePayload,
)




class CodegenRenderingByTagsPublisherFacade:
    """This spec containes different channel operations with specific tags"""

    def __init__(
            self,
            controller: AioPikaBasedAmqpController,
    ) -> None:
        self.__c001_publisher: MessagePublisher[ChannelsC001SubscribeMessagePayload] = controller.bind_publisher(
            encoder=PydanticMessageSerializer(
                model=ChannelsC001SubscribeMessagePayload,  # type: ignore[misc]
            ),
            bindings=AmqpPublisherBindings(
                exchange_name="",
                routing_key="c001",
                is_mandatory=None,
                prefetch_count=None,
            ),
        )
        self.__c003_publisher: MessagePublisher[ChannelsC003SubscribeMessagePayload] = controller.bind_publisher(
            encoder=PydanticMessageSerializer(
                model=ChannelsC003SubscribeMessagePayload,  # type: ignore[misc]
            ),
            bindings=AmqpPublisherBindings(
                exchange_name="",
                routing_key="c003",
                is_mandatory=None,
                prefetch_count=None,
            ),
        )

    async def publish_c001(
            self,
            message: ChannelsC001SubscribeMessagePayload,
    ) -> None:
        await self.__c001_publisher.publish(message)

    async def publish_c003(
            self,
            message: ChannelsC003SubscribeMessagePayload,
    ) -> None:
        await self.__c003_publisher.publish(message)







# @formatter:on
