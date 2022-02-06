# @formatter:off
import abc

from asynchron.amqp.controller import AioPikaBasedAmqpController
from asynchron.amqp.serializer.pydantic import PydanticMessageSerializer
from asynchron.core.amqp import AmqpConsumerBindings
from asynchron.core.consumer import CallableMessageConsumer

from .message import (
    ChannelsC001SubscribeMessagePayload,
)




class CodegenRenderingByTagsConsumerFacade(metaclass=abc.ABCMeta):
    """This spec containes different channel operations with specific tags"""

    def __init__(
            self,
            controller: AioPikaBasedAmqpController,
    ) -> None:
        controller.bind_consumer(
            decoder=PydanticMessageSerializer(
                model=ChannelsC001SubscribeMessagePayload,  # type: ignore[misc]
            ),
            consumer=CallableMessageConsumer(
                consumer=self.consume_c001,
            ),
            bindings=AmqpConsumerBindings(
                exchange_name="",
                binding_keys=(
                    "c001",
                ),
                queue_name=None,
                is_auto_delete_enabled=None,
                is_exclusive=None,
                is_durable=None,
                prefetch_count=None,
            ),
        )

    @abc.abstractmethod
    async def consume_c001(
            self,
            message: ChannelsC001SubscribeMessagePayload,
    ) -> None:
        raise NotImplementedError







# @formatter:on
