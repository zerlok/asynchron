# @formatter:off
import abc

from asynchron.amqp.controller import AioPikaBasedAmqpController
from asynchron.amqp.serializer.pydantic import PydanticMessageSerializer
from asynchron.core.amqp import AmqpConsumerBindings
from asynchron.core.consumer import CallableMessageConsumer

from .message import (
    MainFoo,
)




class ComplexSchemaObjectsConsumerFacade(metaclass=abc.ABCMeta):
    """This configuration contains complex schema objects to test pydantic model codegen"""

    def __init__(
            self,
            controller: AioPikaBasedAmqpController,
    ) -> None:
        controller.bind_consumer(
            decoder=PydanticMessageSerializer(
                model=MainFoo,  # type: ignore[misc]
            ),
            consumer=CallableMessageConsumer(
                consumer=self.consume_foo,
            ),
            bindings=AmqpConsumerBindings(
                exchange_name="foo",
                binding_keys=(
                    "foo",
                ),
                queue_name="foo",
                is_auto_delete_enabled=None,
                is_exclusive=None,
                is_durable=None,
                prefetch_count=None,
            ),
        )

    @abc.abstractmethod
    async def consume_foo(
            self,
            message: MainFoo,
    ) -> None:
        raise NotImplementedError







# @formatter:on
