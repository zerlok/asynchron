__all__ = (
    "JinjaBasedPythonAioPikaCodeGenerator",
)

import re
import typing as t
from dataclasses import dataclass, field
from pathlib import Path

import stringcase  # type: ignore
from pydantic.fields import FieldInfo

from asynchron.codegen.app import AsyncApiCodeGenerator
from asynchron.codegen.generator.jinja.renderer import JinjaTemplateRenderer
from asynchron.codegen.info import AsyncApiCodeGeneratorMetaInfo
from asynchron.codegen.spec.base import (
    AMQPBindingTrait,
    AsyncAPIObject,
    ChannelBindingsObject, ChannelItemObject,
    MessageObject,
    OperationBindingsObject, OperationObject,
    SchemaObject,
)
from asynchron.strict_typing import as_, as_sequence

K = t.TypeVar("K", bound=t.Hashable)
V = t.TypeVar("V")
T = t.TypeVar("T")


@dataclass(frozen=True)
class TypeDef:
    name: str
    nested: t.Sequence["TypeDef"] = field(default_factory=tuple)


class TypeTraits:
    ANY: t.Final[TypeDef] = TypeDef("typing.Any")
    NONE: t.Final[TypeDef] = TypeDef("None")
    BOOL: t.Final[TypeDef] = TypeDef("bool")
    INT: t.Final[TypeDef] = TypeDef("int")
    FLOAT: t.Final[TypeDef] = TypeDef("float")
    NUMBER: t.Final[TypeDef] = TypeDef("typing.Union", (INT, FLOAT,))
    STR: t.Final[TypeDef] = TypeDef("str")

    @classmethod
    def create_optional(cls, type_: TypeDef) -> TypeDef:
        return TypeDef("typing.Optional", (type_,))

    @classmethod
    def create_union(cls, options: t.Iterable[TypeDef]) -> TypeDef:
        return TypeDef("typing.Union", tuple(options))

    @classmethod
    def create_literal(cls, options: t.Iterable[t.Union[int, str]]) -> TypeDef:
        return TypeDef(f"""typing.Literal["{'", "'.join(str(option) for option in options)}"]""")

    @classmethod
    def create_collection(cls, item: TypeDef) -> TypeDef:
        return TypeDef("typing.Collection", (item,))

    @classmethod
    def create_sequence(cls, item: TypeDef) -> TypeDef:
        return TypeDef("typing.Sequence", (item,))

    @classmethod
    def create_mapping(cls, key: TypeDef, value: TypeDef) -> TypeDef:
        return TypeDef("typing.Mapping", (key, value,))


@dataclass(frozen=True)
class MessageFieldDef:
    type_: TypeDef
    info: FieldInfo


@dataclass(frozen=True)
class MessageDef:
    name: str
    description: t.Optional[str]
    fields: t.Mapping[str, MessageFieldDef]


@dataclass(frozen=True)
class ConsumerDef:
    name: str
    description: t.Optional[str]
    message: MessageDef
    exchange_name: str
    queue_name: t.Optional[str]
    binding_keys: t.Collection[str]


@dataclass(frozen=True)
class PublisherDef:
    name: str
    description: t.Optional[str]
    message: MessageDef
    exchange_name: str
    routing_key: str
    is_mandatory: t.Optional[bool]


@dataclass(frozen=True)
class ModuleDef:
    python_path: str
    fs_path: Path
    description: t.Optional[str]
    imports: t.Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class AppDef:
    name: str
    description: t.Optional[str]
    modules: t.Mapping[str, ModuleDef]
    consumers: t.Collection[ConsumerDef]
    publishers: t.Collection[PublisherDef]
    messages: t.Collection[MessageDef]


@dataclass(frozen=True)
class AmqpConsumerOperation:
    name: str
    channel: ChannelItemObject
    operation: OperationObject
    messages: t.Sequence[MessageObject]
    exchange_name: str
    exchange_type: str
    queue_name: str
    binding_keys: t.Collection[str]

    channel_binding: AMQPBindingTrait.AMQPChannelBindingObject
    operation_binding: AMQPBindingTrait.AMQPOperationBindingObject


@dataclass(frozen=True)
class AmqpPublisherOperation:
    name: str
    channel: ChannelItemObject
    operation: OperationObject
    messages: t.Sequence[MessageObject]
    exchange_name: str
    exchange_type: str
    routing_key: str

    channel_binding: AMQPBindingTrait.AMQPChannelBindingObject
    operation_binding: AMQPBindingTrait.AMQPOperationBindingObject


class JinjaBasedPythonAioPikaCodeGenerator(AsyncApiCodeGenerator):
    __JINJA_TEMPLATES_DIR: t.Final[Path] = Path(__file__).parent / "templates"

    def __init__(
            self,
            meta: AsyncApiCodeGeneratorMetaInfo,
            renderer: t.Optional[JinjaTemplateRenderer] = None,
    ) -> None:
        self.__meta = meta
        self.__renderer = renderer or JinjaTemplateRenderer(self.__JINJA_TEMPLATES_DIR)

    def generate(self, config: AsyncAPIObject) -> t.Iterable[t.Tuple[Path, t.Iterable[str]]]:
        messages: t.Mapping[object, MessageDef] = {
            channel_name: message
            for channel_name, message in self.__iter_message_defs(config)
        }

        app_name = self.__normalize_name(config.info.title)
        app = AppDef(
            name=app_name,
            description=config.info.description,
            modules=self.__get_app_modules(),
            consumers=list(self.__iter_amqp_consumer_defs(config, messages)),
            publishers=list(self.__iter_amqp_publisher_defs(config, messages)),
            messages=list(messages.values()),
        )

        for module_name, module in app.modules.items():
            yield module.fs_path, self.__renderer.render(name=module_name, module=module, app=app, meta=self.__meta)

    def __get_app_modules(self) -> t.Mapping[str, ModuleDef]:
        def define_module(name: str) -> ModuleDef:
            return ModuleDef(
                python_path=f"{self.__meta.project_name}.{name}" if self.__meta.use_absolute_imports else f".{name}",
                description=None,
                fs_path=Path(f"{name}.py"),
            )

        return {
            name: define_module(name)
            for name in (
                "__init__",
                # "__main__",
                "message",
                "consumer",
                "publisher",
            )
        }

    def __iter_message_defs(self, config: AsyncAPIObject) -> t.Iterable[t.Tuple[str, MessageDef]]:
        for channel_name, channel, operation in config.iter_channel_operations():
            # TODO: support message sequence
            message = as_(MessageObject, operation.message)
            if message is None:
                continue

            payload = as_(SchemaObject, message.payload)
            if payload is None:
                continue

            properties = payload.properties
            if properties is None:
                continue

            yield channel_name, MessageDef(
                name=self.__join_name((channel_name, message.title or "message")),
                description=message.description,
                fields={
                    self.__normalize_name(name): self.__get_field_def(
                        schema=schema,
                        alias=name,
                        is_optional=not payload.required or name not in payload.required,
                    )
                    for name, schema in properties.items()
                },
            )

    def __iter_amqp_operations(
            self,
            operations: t.Iterable[t.Tuple[str, ChannelItemObject, OperationObject]],
    ) -> t.Iterable[t.Tuple[str, ChannelItemObject, OperationObject, AMQPBindingTrait.AMQPChannelBindingObject,
                            AMQPBindingTrait.AMQPOperationBindingObject]]:
        for channel_name, channel, operation in operations:
            channel_bindings = as_(ChannelBindingsObject, channel.bindings)
            if channel_bindings is None:
                continue

            operation_bindings = as_(OperationBindingsObject, operation.bindings)
            if operation_bindings is None:
                continue

            amqp_channel_bindings = as_(AMQPBindingTrait.AMQPChannelBindingObject, channel_bindings.amqp)
            amqp_operation_bindings = as_(AMQPBindingTrait.AMQPOperationBindingObject, operation_bindings.amqp)
            if amqp_channel_bindings is None or amqp_operation_bindings is None:
                continue

            yield channel_name, channel, operation, amqp_channel_bindings, amqp_operation_bindings

    def __iter_amqp_consumer_defs(
            self,
            config: AsyncAPIObject,
            messages: t.Mapping[object, MessageDef],
    ) -> t.Iterable[ConsumerDef]:
        publishes = self.__iter_amqp_operations(config.iter_channel_publish_operations())

        for channel_name, channel, publish, channel_bindings, operation_bindings in publishes:
            exchange = as_(AMQPBindingTrait.AMQPChannelBindingObject.Exchange, channel_bindings.exchange)
            queue = as_(AMQPBindingTrait.AMQPChannelBindingObject.Queue, channel_bindings.queue)
            binding_keys = operation_bindings.cc
            if exchange is None or queue is None or binding_keys is None:
                continue

            yield ConsumerDef(
                name=self.__normalize_name(channel_name),
                description=channel.description,
                exchange_name=exchange.name,
                queue_name=queue.name,
                binding_keys=binding_keys,
                message=messages[channel_name],
            )

    def __iter_amqp_publisher_defs(
            self,
            config: AsyncAPIObject,
            messages: t.Mapping[object, MessageDef],
    ) -> t.Iterable[PublisherDef]:
        subscribes = self.__iter_amqp_operations(config.iter_channel_subscribe_operations())

        for channel_name, channel, subscribe, channel_bindings, operation_bindings in subscribes:
            exchange = as_(AMQPBindingTrait.AMQPChannelBindingObject.Exchange, channel_bindings.exchange)

            binding_keys = operation_bindings.cc or []
            routing_key = binding_keys[0] if len(binding_keys) == 1 else None

            if exchange is None or routing_key is None:
                continue

            yield PublisherDef(
                name=self.__normalize_name(channel_name),
                description=channel.description,
                exchange_name=exchange.name,
                routing_key=routing_key,
                message=messages[channel_name],
                is_mandatory=operation_bindings.mandatory,
            )

    def __normalize_name(self, value: str) -> str:
        x = re.sub(r"[^A-Za-z0-9_]+", "_", value)
        x = stringcase.snakecase(x)
        x = re.sub(r"_+", "_", x)
        x = re.sub(r"^_?(.*?)_$", "\1", x)
        return x

    def __join_name(self, values: t.Sequence[str]) -> str:
        return "_".join((self.__normalize_name(v) for v in values))

    def __split_on_messages(
            self,
            messages: t.Collection[MessageObject],
    ) -> t.Iterable[t.Tuple[SchemaObject, t.Mapping[str, SchemaObject]]]:
        for message in messages:
            payload = as_(SchemaObject, message.payload)
            if payload is None:
                continue

            properties = payload.properties
            if properties is None:
                continue

            yield payload, properties

            # TODO: build messages from nested objects
            # visited = {}
            # stack: t.List[t.Tuple[t.Sequence[str], SchemaObject]] = [((), payload)]
            # while stack:
            #     path, info = stack.pop(0)
            #
            #     if isinstance(info.items, SchemaObject):
            #         stack.append(((*path, "item",), info.items,))
            #
            #     elif isinstance(info.items, t.Sequence):
            #         for subinfo in info.items:
            #             stack.append(((*path, subinfo.title or "item",), subinfo,))
            #
            #     if info.all_of is not None:
            #         for subinfo in info.all_of:
            #             stack.append(((*path, subinfo.title or "item",), subinfo,))
            #
            #     if info.any_of is not None:
            #         for subinfo in info.any_of:
            #             stack.append(((*path, subinfo.title or "item",), subinfo,))
            #
            #     if info.one_of is not None:
            #         for subinfo in info.one_of:
            #             stack.append(((*path, subinfo.title or "item",), subinfo,))
            #
            #     for name, subinfo in (info.properties or {}).items():
            #         if subinfo.type_ == "object" and subinfo.properties is not None:
            #             stack.append(((*path, subinfo.title or "value",), subinfo,))
            #             # visited[(*path, "Item",)] = info
            #
            # print(stack)

    def __get_field_def(
            self,
            schema: SchemaObject,
            alias: t.Optional[str] = None,
            is_optional: bool = False,
    ) -> MessageFieldDef:
        field_type = self.__get_field_type(schema)
        if is_optional:
            field_type = TypeTraits.create_optional(field_type)

        return MessageFieldDef(
            type_=field_type,
            info=FieldInfo(
                default=schema.default,
                alias=alias,
                title=schema.title,
                description=schema.description,
                const=None,
                gt=schema.exclusive_minimum,
                ge=schema.minimum,
                lt=schema.exclusive_maximum,
                le=schema.maximum,
                multiple_of=schema.multiple_of,
                min_items=schema.min_items,
                max_items=schema.max_items,
                min_length=schema.min_length,
                max_length=schema.max_length,
                allow_mutation=False,
                regex=schema.pattern,
            ),
        )

    def __get_field_type(self, value: t.Optional[SchemaObject]) -> TypeDef:
        if value is None:
            return TypeTraits.ANY

        if value.type_ == "null":
            result = TypeTraits.NONE

        elif value.type_ == "boolean":
            result = TypeTraits.BOOL

        elif value.type_ == "number":
            result = TypeTraits.NUMBER

        elif value.type_ == "integer":
            result = TypeTraits.INT

        elif value.type_ == "string":
            result = TypeTraits.STR

        elif value.type_ == "array":
            assert isinstance(value.items, SchemaObject)
            item = self.__get_field_type(value.items)

            if value.unique_items:
                result = TypeTraits.create_collection(item)
            else:
                result = TypeTraits.create_sequence(item)

        elif value.type_ == "object":
            result = TypeTraits.create_mapping(TypeTraits.STR, TypeTraits.ANY)

        elif options := as_sequence(SchemaObject, value.type_):
            result = TypeTraits.create_union(self.__get_field_type(option) for option in options)

        elif value.enum is not None:
            result = TypeTraits.create_literal(value.enum)

        else:
            raise ValueError(value)

        # if value.nullable:
        #     result = TypeTraits.create_optional(result)

        return result
