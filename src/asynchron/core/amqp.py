import typing as t
from dataclasses import dataclass


@dataclass(frozen=True)
class AmqpServerBindings:
    connection_url: str


@dataclass(frozen=True)
class AmqpConsumerBindings:
    exchange_name: str
    binding_keys: t.Collection[str]
    exchange_type: t.Optional[t.Literal["fanout", "direct", "topic", "headers"]] = None
    queue_name: t.Optional[str] = None
    is_auto_delete_enabled: t.Optional[bool] = None
    is_exclusive: t.Optional[bool] = None
    is_durable: t.Optional[bool] = None
    prefetch_count: t.Optional[int] = None


@dataclass(frozen=True)
class AmqpPublisherBindings:
    exchange_name: str
    routing_key: str
    exchange_type: t.Optional[t.Literal["fanout", "direct", "topic", "headers"]] = None
    is_mandatory: t.Optional[bool] = None
    prefetch_count: t.Optional[int] = None
    # is_auto_delete_enabled: t.Optional[bool] = None
    # is_durable: t.Optional[bool] = None
