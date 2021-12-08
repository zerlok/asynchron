__all__ = (
    "JinjaBasedPythonAioPikaCodeGenerator",
)

import re
import typing as t
from dataclasses import dataclass, field
from pathlib import Path

import stringcase  # type: ignore
from pydantic.fields import FieldInfo

from asynchron.app import AsyncApiCodeGenerator
from asynchron.spec.base import (
    AMQPBindingTrait,
    AsyncAPIObject,
    ChannelBindingsObject, ChannelItemObject,
    MessageObject,
    OperationBindingsObject, OperationObject,
    SchemaObject,
)
from asynchron.spec.code_generator.info import AsyncApiCodeGeneratorMetaInfo
from asynchron.spec.code_generator.jinja.renderer import JinjaTemplateRenderer
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
class ManagerDef:
    name: str
    description: t.Optional[str]


@dataclass(frozen=True)
class ModuleDef:
    description: t.Optional[str]
    python_path: str
    fs_path: Path
    aliases: t.Mapping[str, str] = field(default_factory=dict)
    imports: t.Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class AppDef:
    name: str
    description: t.Optional[str]
    modules: t.Mapping[str, ModuleDef]
    consumers: t.Collection[ConsumerDef]
    messages: t.Collection[MessageDef]
    manager: ManagerDef


@dataclass(frozen=True)
class AmqpConsumerOperation:
    name: str
    channel: ChannelItemObject
    operation: OperationObject
    messages: t.Sequence[MessageObject]
    exchange_name: str
    queue_name: str
    binding_keys: t.Collection[str]

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
        app_messages: t.List[MessageDef] = []
        app_consumers: t.List[ConsumerDef] = []
        for op in self.__iter_amqp_publish_operations(config):
            consumer, messages = self.__create_consumer_def(op)
            app_consumers.append(consumer)
            app_messages.extend(messages)

        app = AppDef(
            name=config.info.title,
            description=config.info.description,
            modules=self.__get_app_modules(),
            consumers=app_consumers,
            messages=app_messages,
            manager=ManagerDef(
                name=config.info.title,
                description=config.info.description,
            ),
        )

        for module_name, module in app.modules.items():
            yield module.fs_path, self.__renderer.render(name=module_name, module=module, app=app, meta=self.__meta)

    def __get_app_modules(self) -> t.Mapping[str, ModuleDef]:
        return {
            "__init__": ModuleDef(
                python_path=f"{self.__meta.project_name}.__init__",
                description=None,
                fs_path=Path("__init__.py"),
            ),
            "__main__": ModuleDef(
                python_path=f"{self.__meta.project_name}.__main__",
                description=None,
                fs_path=Path("__main__.py"),
            ),
            "message": ModuleDef(
                python_path=f"{self.__meta.project_name}.message",
                description=None,
                fs_path=Path("message.py"),
            ),
            "consumer": ModuleDef(
                python_path=f"{self.__meta.project_name}.consumer",
                description=None,
                fs_path=Path("consumer.py"),
            ),
        }

    def __iter_amqp_publish_operations(self, config: AsyncAPIObject) -> t.Iterable[AmqpConsumerOperation]:
        for _, channels in config.channels:
            for channel_name, channel in channels.items():
                publish = as_(OperationObject, channel.publish)
                channel_bindings = as_(ChannelBindingsObject, channel.bindings)

                if publish is None or channel_bindings is None:
                    continue

                operation_bindings = as_(OperationBindingsObject, publish.bindings)
                if operation_bindings is None:
                    continue

                amqp_operation_bindings = as_(AMQPBindingTrait.AMQPOperationBindingObject, operation_bindings.amqp)
                amqp_channel_bindings = as_(AMQPBindingTrait.AMQPChannelBindingObject, channel_bindings.amqp)
                if amqp_operation_bindings is None or amqp_channel_bindings is None:
                    continue

                message = as_(MessageObject, publish.message)
                messages = as_sequence(MessageObject, publish.message)
                if message is not None:
                    messages = (message,)

                if messages is None:
                    continue

                exchange = as_(AMQPBindingTrait.AMQPChannelBindingObject.Exchange, amqp_channel_bindings.exchange)
                queue = as_(AMQPBindingTrait.AMQPChannelBindingObject.Queue, amqp_channel_bindings.queue)
                binding_keys = amqp_operation_bindings.cc
                if exchange is None or queue is None or binding_keys is None:
                    continue

                queue_name = as_(str, queue.name)
                if queue_name is None:
                    continue

                yield AmqpConsumerOperation(
                    name=self.__normalize_name(channel_name),
                    channel=channel,
                    operation=publish,
                    messages=messages,
                    exchange_name=exchange.name,
                    queue_name=queue_name,
                    binding_keys=binding_keys,
                    channel_binding=amqp_channel_bindings,
                    operation_binding=amqp_operation_bindings,
                )

    def __normalize_name(self, value: str) -> str:
        # re.compile(r"[^A-Za-z0-9_]")
        x = re.sub(r"[^A-Za-z0-9_]+", "_", value)
        x = stringcase.snakecase(x)
        # x = re.sub(r"([a-z][A-Z])", lambda m: "_".join(m.group(1)).lower(), x)
        x = re.sub(r"_+", "_", x)
        x = re.sub(r"^_?(.*?)_$", "\1", x)
        return x

    def __join_name(self, values: t.Sequence[str]) -> str:
        return "_".join(values)

    def __create_consumer_def(self, operation: AmqpConsumerOperation) -> t.Tuple[ConsumerDef, t.Sequence[MessageDef]]:
        messages = tuple(
            MessageDef(
                name=self.__join_name((operation.name, self.__normalize_name(message.title or "message"))),
                description=message.description,
                fields={
                    self.__normalize_name(name): self.__get_field_def(
                        schema=schema,
                        alias=name,
                        is_optional=not message.required or name in message.required,
                    )
                    for name, schema in properties.items()
                },
            )
            for message, properties in self.__split_on_messages(operation.messages)
        )

        return ConsumerDef(
            name=operation.name,
            description=operation.channel.description,
            exchange_name=operation.exchange_name,
            queue_name=operation.queue_name,
            binding_keys=operation.binding_keys,
            message=messages[0],
        ), messages

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
            raise ValueError

        # if value.nullable:
        #     result = TypeTraits.create_optional(result)

        return result
