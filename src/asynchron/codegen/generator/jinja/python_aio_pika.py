__all__ = (
    "JinjaBasedPythonAioPikaCodeGenerator",
)

import re
import typing as t
from dataclasses import dataclass, field, replace
from pathlib import Path

import stringcase  # type: ignore
from pydantic.fields import FieldInfo

from asynchron.codegen.app import AsyncApiCodeGenerator
from asynchron.codegen.generator.jinja.jinja_renderer import JinjaTemplateRenderer
from asynchron.codegen.info import AsyncApiCodeGeneratorMetaInfo
from asynchron.codegen.spec.base import (
    AMQPBindingTrait,
    AsyncAPIObject,
    ChannelBindingsObject, ChannelItemObject,
    MessageObject,
    OperationBindingsObject, OperationObject,
    SchemaObject,
)
from asynchron.strict_typing import as_, as_mapping, as_sequence

K = t.TypeVar("K", bound=t.Hashable)
V = t.TypeVar("V")
T = t.TypeVar("T")


@dataclass(frozen=True)
class Expr:
    value: str


@dataclass(frozen=True)
class RequirementDef:
    path: t.Sequence[str]
    alias: str

    @classmethod
    def build(cls, alias: str, *path: str) -> "RequirementDef":
        return cls(path or (alias,), alias)

    @classmethod
    def build_alias(cls, alias: str, *path: str) -> "RequirementDef":
        return cls(path, alias)

    @classmethod
    def merge(
            cls,
            *values: t.Optional[t.Union["RequirementDef", t.Iterable[t.Optional["RequirementDef"]]]],
    ) -> t.Collection["RequirementDef"]:
        return tuple(set(
            requirement
            for value in values
            for requirement in (value if isinstance(value, t.Iterable) else (value,))
            if requirement is not None
        ))


@dataclass(frozen=True)
class TypeDef:
    name: str
    requires: t.Collection[RequirementDef]


@dataclass(frozen=True)
class TypeDefAlias(TypeDef):
    type_vars: t.Sequence["TypeDef"]

    @classmethod
    def from_module_attribute(
            cls,
            module: RequirementDef,
            attribute: str,
            type_vars: t.Optional[t.Sequence["TypeDef"]] = None,
    ) -> "TypeDef":
        return cls(
            name=".".join((module.alias, attribute)),
            type_vars=type_vars,
            requires=(module, *(requirement for subtype in (type_vars or ()) for requirement in subtype.requires)),
        )


class Traits:
    IMPORT_TYPING: t.Final[RequirementDef] = RequirementDef.build("typing")
    IMPORT_DATETIME: t.Final[RequirementDef] = RequirementDef.build("datetime")
    IMPORT_UUID: t.Final[RequirementDef] = RequirementDef.build("uuid")
    IMPORT_ENUM: t.Final[RequirementDef] = RequirementDef.build("enum")
    IMPORT_PYDANTIC: t.Final[RequirementDef] = RequirementDef.build("pydantic")

    TYPE_NONE: t.Final[TypeDef] = TypeDef("None", ())
    TYPE_BYTES: t.Final[TypeDef] = TypeDef("bytes", ())
    TYPE_BOOL: t.Final[TypeDef] = TypeDef("bool", ())
    TYPE_INT: t.Final[TypeDef] = TypeDef("int", ())
    TYPE_FLOAT: t.Final[TypeDef] = TypeDef("float", ())
    TYPE_STR: t.Final[TypeDef] = TypeDef("str", ())

    TYPE_ANY: t.Final[TypeDef] = TypeDefAlias.from_module_attribute(IMPORT_TYPING, "Any")
    TYPE_NUMBER: t.Final[TypeDef] = TypeDefAlias.from_module_attribute(IMPORT_TYPING, "Union", (TYPE_INT, TYPE_FLOAT,))

    TYPE_ENUM: t.Final[TypeDef] = TypeDefAlias.from_module_attribute(IMPORT_ENUM, "Enum")

    TYPE_DATE: t.Final[TypeDef] = TypeDefAlias.from_module_attribute(IMPORT_DATETIME, "date")
    TYPE_TIME: t.Final[TypeDef] = TypeDefAlias.from_module_attribute(IMPORT_DATETIME, "time")
    TYPE_DATETIME: t.Final[TypeDef] = TypeDefAlias.from_module_attribute(IMPORT_DATETIME, "datetime")

    TYPE_URI: t.Final[TypeDef] = TYPE_STR

    TYPE_UUID: t.Final[TypeDef] = TypeDefAlias.from_module_attribute(IMPORT_UUID, "UUID")

    TYPE_PYDANTIC_BASE_MODEL: t.Final[TypeDef] = TypeDefAlias.from_module_attribute(IMPORT_PYDANTIC, "BaseModel")

    @classmethod
    def create_optional(cls, type_: TypeDef) -> TypeDef:
        return TypeDefAlias.from_module_attribute(cls.IMPORT_TYPING, "Optional", (type_,))

    @classmethod
    def create_union(cls, options: t.Iterable[TypeDef]) -> TypeDef:
        return TypeDefAlias.from_module_attribute(cls.IMPORT_TYPING, "Union", tuple(options))

    @classmethod
    def create_literal(cls, options: t.Iterable[t.Union[int, str]]) -> TypeDef:
        return TypeDefAlias.from_module_attribute(
            module=cls.IMPORT_TYPING,
            attribute=f"""Literal[{", ".join(repr(option) for option in options)}]""",
        )

    @classmethod
    def create_collection(cls, item: TypeDef) -> TypeDef:
        return TypeDefAlias.from_module_attribute(cls.IMPORT_TYPING, "Collection", (item,))

    @classmethod
    def create_sequence(cls, item: TypeDef) -> TypeDef:
        return TypeDefAlias.from_module_attribute(cls.IMPORT_TYPING, "Sequence", (item,))

    @classmethod
    def create_mapping(cls, key: TypeDef, value: TypeDef) -> TypeDef:
        return TypeDefAlias.from_module_attribute(cls.IMPORT_TYPING, "Mapping", (key, value,))


@dataclass(frozen=True)
class MessageDef(TypeDef):
    description: t.Optional[str]
    bases: t.Sequence[TypeDef]


@dataclass(frozen=True)
class EnumMessageDef(MessageDef):
    literals: t.Sequence[t.Tuple[Expr, Expr]]

    @classmethod
    def build_enum(
            cls,
            name: str,
            literals: t.Iterable[t.Tuple[Expr, Expr]],
            description: t.Optional[str] = None,
            bases: t.Optional[t.Sequence[TypeDef]] = None,
    ) -> "EnumMessageDef":
        clean_bases = list(bases or ())
        clean_bases.append(Traits.TYPE_ENUM)

        return cls(
            name=name,
            requires=Traits.TYPE_ENUM.requires,
            description=description,
            bases=clean_bases,
            literals=tuple(literals),
        )


@dataclass(frozen=True)
class ObjectMessageDef(MessageDef):
    @dataclass(frozen=True)
    class FieldDef:
        type_: TypeDef
        info: FieldInfo

    fields: t.Sequence[t.Tuple[str, FieldDef]]


@dataclass(frozen=True)
class PydanticModelMessageDef(ObjectMessageDef):

    @classmethod
    def build(
            cls,
            name: str,
            requires: t.Optional[t.Collection[RequirementDef]] = None,
            description: t.Optional[str] = None,
            bases: t.Optional[t.Sequence[TypeDef]] = None,
            fields: t.Optional[t.Iterable[t.Tuple[str, ObjectMessageDef.FieldDef]]] = None,
    ) -> "PydanticModelMessageDef":
        clean_fields = tuple(fields) if fields else ()
        clean_bases = list(bases or ())
        clean_bases.append(Traits.TYPE_PYDANTIC_BASE_MODEL)

        return cls(
            name=name,
            requires=RequirementDef.merge(
                requires,
                *(i.requires for i in clean_bases),
                *(f.type_.requires for _, f in clean_fields),
            ),
            description=description,
            bases=tuple(clean_bases),
            fields=clean_fields,
        )


@dataclass(frozen=True)
class UnionMessageDef(MessageDef):
    options: t.Sequence[TypeDef]


@dataclass(frozen=True)
class ConsumerDef:
    name: str
    description: t.Optional[str]
    message: MessageDef
    exchange_name: str
    queue_name: t.Optional[str]
    binding_keys: t.Collection[str]
    requires: t.Collection[RequirementDef] = field(default_factory=tuple)


@dataclass(frozen=True)
class PublisherDef:
    name: str
    description: t.Optional[str]
    message: MessageDef
    exchange_name: str
    routing_key: str
    is_mandatory: t.Optional[bool]
    requires: t.Collection[RequirementDef] = field(default_factory=tuple)


@dataclass(frozen=True)
class ModuleDef:
    path: t.Sequence[str]
    description: t.Optional[str]
    requires: t.Collection[RequirementDef] = field(default_factory=tuple)


@dataclass(frozen=True)
class AppDef:
    name: str
    description: t.Optional[str]
    modules: t.Collection[ModuleDef]
    consumers: t.Collection[ConsumerDef]
    publishers: t.Collection[PublisherDef]
    messages: t.Collection[MessageDef]


class JinjaBasedPythonAioPikaCodeGenerator(AsyncApiCodeGenerator):
    __JINJA_TEMPLATES_DIR: t.Final[Path] = Path(__file__).parent / "templates"

    def __init__(
            self,
            meta: AsyncApiCodeGeneratorMetaInfo,
            renderer: t.Optional[JinjaTemplateRenderer] = None,
    ) -> None:
        self.__meta = meta
        self.__renderer = renderer or JinjaTemplateRenderer.from_template_root_dir(self.__JINJA_TEMPLATES_DIR)

    def generate(self, config: AsyncAPIObject) -> t.Iterable[t.Tuple[Path, t.Iterable[str]]]:
        channel_messages: t.Dict[str, MessageDef] = {}
        app_messages: t.List[MessageDef] = []
        for channel_name, channel_message_def, message_defs in self.__iter_message_defs(config):
            channel_messages[channel_name] = channel_message_def
            app_messages.extend(message_defs)

        app_consumers = list(self.__iter_amqp_consumer_defs(config, channel_messages))
        app_publishers = list(self.__iter_amqp_publisher_defs(config, channel_messages))
        app_modules = list(self.__get_app_modules(app_messages, app_consumers, app_publishers))

        app = AppDef(
            name=self.__normalize_name(config.info.title),
            description=config.info.description,
            modules=app_modules,
            consumers=app_consumers,
            publishers=app_publishers,
            messages=app_messages,
        )

        for module in app.modules:
            module_path = Path(*module.path, ".py")
            stream = self.__renderer.render(
                name=module.path[-1],
                context={
                    "module": module,
                    "app": app,
                    "meta": self.__meta,
                },
            )

            yield module_path, stream

    def __get_app_modules(
            self,
            messages: t.Sequence[MessageDef],
            consumers: t.Sequence[ConsumerDef],
            publishers: t.Sequence[PublisherDef],
    ) -> t.Iterable[ModuleDef]:
        return (
            ModuleDef(
                path=("__init__",),
                description=None,
                requires=(),
            ),
            ModuleDef(
                path=("consumer",),
                description=None,
                requires=[
                    requirement
                    for message in messages
                    for requirement in message.requires
                ],
            ),
            ModuleDef(
                path=("publisher",),
                description=None,
                requires=[
                    requirement
                    for message in messages
                    for requirement in message.requires
                ],
            ),
            ModuleDef(
                path=("message",),
                description=None,
                requires=[
                    requirement
                    for message in messages
                    for requirement in message.requires
                ],
            ),
        )

    def __iter_message_defs(
            self,
            config: AsyncAPIObject,
    ) -> t.Iterable[t.Tuple[str, MessageDef, t.Sequence[MessageDef]]]:
        for channel_name, channel, operation in config.iter_channel_operations():
            # TODO: support message sequence
            message = as_(MessageObject, operation.message)
            if message is None:
                continue

            payload = as_(SchemaObject, message.payload)
            if payload is None:
                continue

            channel_message_name = message.title or self.__join_name((channel_name, "message"))
            *_, channel_message_def = message_defs = self.__split_by_message_defs(channel_message_name, payload)

            yield channel_name, channel_message_def, message_defs

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
            messages: t.Mapping[str, MessageDef],
    ) -> t.Iterable[ConsumerDef]:
        publishes = self.__iter_amqp_operations(config.iter_channel_publish_operations())

        for channel_name, channel, publish, channel_bindings, operation_bindings in publishes:
            exchange = as_(AMQPBindingTrait.AMQPChannelBindingObject.Exchange, channel_bindings.exchange)
            queue = as_(AMQPBindingTrait.AMQPChannelBindingObject.Queue, channel_bindings.queue)
            binding_keys = operation_bindings.cc
            if exchange is None or queue is None or binding_keys is None:
                continue

            channel_message = messages[channel_name]
            yield ConsumerDef(
                name=self.__normalize_name(channel_name),
                description=channel.description,
                exchange_name=exchange.name,
                queue_name=queue.name,
                binding_keys=binding_keys,
                message=channel_message,
                requires=channel_message.requires,
            )

    def __iter_amqp_publisher_defs(
            self,
            config: AsyncAPIObject,
            messages: t.Mapping[str, MessageDef],
    ) -> t.Iterable[PublisherDef]:
        subscribes = self.__iter_amqp_operations(config.iter_channel_subscribe_operations())

        for channel_name, channel, subscribe, channel_bindings, operation_bindings in subscribes:
            exchange = as_(AMQPBindingTrait.AMQPChannelBindingObject.Exchange, channel_bindings.exchange)

            binding_keys = operation_bindings.cc or []
            routing_key = binding_keys[0] if len(binding_keys) == 1 else None

            if exchange is None or routing_key is None:
                continue

            channel_message = messages[channel_name]
            yield PublisherDef(
                name=self.__normalize_name(channel_name),
                description=channel.description,
                exchange_name=exchange.name,
                routing_key=routing_key,
                is_mandatory=operation_bindings.mandatory,
                message=channel_message,
                requires=channel_message.requires,
            )

    def __normalize_name(self, value: str) -> str:
        x = re.sub(r"[^A-Za-z0-9_]+", "_", value)
        x = stringcase.snakecase(x)
        x = re.sub(r"_+", "_", x)
        x = re.sub(r"^_?(.*?)_$", "\1", x)
        return x

    def __join_name(self, values: t.Sequence[str]) -> str:
        return "_".join((self.__normalize_name(v) for v in values))

    def __split_by_message_defs(self, head: str, payload: SchemaObject) -> t.Sequence[MessageDef]:
        result: t.List[MessageDef] = []
        queue: t.List[t.Tuple[str, t.Sequence[TypeDef], SchemaObject]] = [(head, (), payload)]

        while queue:
            prefix, bases, item = queue.pop(0)
            inherits: t.List[TypeDef] = list(bases)
            subtypes: t.List[MessageDef] = []

            if parts := as_sequence(SchemaObject, item.all_of):
                for i, part in enumerate(parts):
                    name = self.__join_name((prefix, "part", str(i)))
                    inherits.append(TypeDef(name))
                    queue.append((name, bases, part))

                parts_name = self.__join_name((prefix, "parts"))
                inherits.append(TypeDef(parts_name))
                subtypes.append(MessageDef(
                    name=parts_name,
                    description=item.description,
                    inherits=inherits,
                    requires=(),
                ))

            if parts := as_sequence(SchemaObject, item.any_of):
                options: t.List[TypeDef] = []

                for i, part in enumerate(parts):
                    name = self.__join_name((prefix, "option", str(i)))
                    options.append(TypeDef(name))
                    queue.append((name, tuple(inherits), part))

                union_name = self.__join_name((prefix, "options"))
                inherits.append(TypeDef(union_name))
                subtypes.append(UnionMessageDef(
                    name=union_name,
                    description=item.description,
                    inherits=inherits,
                    options=options,
                    requires=(),
                ))

            if parts := as_sequence(SchemaObject, item.one_of):
                options: t.List[TypeDef] = []

                for i, part in enumerate(parts):
                    name = self.__join_name((prefix, "alternative", str(i)))
                    options.append(TypeDef(name))
                    queue.append((name, tuple(inherits), part))

                union_name = self.__join_name((prefix, "alternatives"))
                inherits.append(TypeDef(union_name))
                subtypes.append(UnionMessageDef(
                    name=union_name,
                    description=item.description,
                    inherits=inherits,
                    options=options,
                    requires=(),
                ))

            if item.enum is not None:
                enum_def = EnumMessageDef.build_enum(
                    name=self.__join_name((prefix, "enum")),
                    description=item.description,
                    inherits=inherits,
                    literals=item.enum,
                    requires=...,
                )
                inherits.append(enum_def.name)
                subtypes.append(enum_def)

            if properties := as_mapping(str, SchemaObject, item.properties):
                object_name = self.__join_name((prefix, "object"))
                inherits.append(object_name)
                subtypes.append(ObjectMessageDef.build_pydantic_model(
                    name=object_name,
                    description=item.description,
                    inherits=inherits,
                    fields=(
                        (self.__normalize_name(name), self.__get_field_def(
                            schema=schema,
                            alias=name,
                            is_optional=not item.required or name not in item.required,
                        ))
                        for name, schema in properties.items()
                    ),
                ))

            if not subtypes:
                continue

            elif len(subtypes) == 1:
                result.append(replace(subtypes[0], name=prefix, inherits=subtypes[0].inherits[:-1]))

            else:
                result.extend(subtypes)
                result.append(MessageDef(
                    name=prefix,
                    description=item.description,
                    inherits=inherits,
                ))

        return list(reversed(result))

    def __iter_message_payload_properties(
            self,
            payload: t.Optional[SchemaObject],
    ) -> t.Iterable[t.Tuple[str, SchemaObject]]:
        if payload is not None:
            if properties := as_mapping(str, SchemaObject, payload.properties):
                for name, schema in properties.items():
                    yield

            if parts := as_sequence(SchemaObject, payload.all_of):
                for part in parts:
                    yield from self.__iter_message_payload_properties(part)

    def __get_field_def(
            self,
            schema: SchemaObject,
            alias: t.Optional[str] = None,
            is_optional: bool = False,
    ) -> ObjectMessageDef.FieldDef:
        field_type = self.__get_field_type(schema)
        if is_optional:
            field_type = Traits.create_optional(field_type)

        return ObjectMessageDef.FieldDef(
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
            return Traits.TYPE_ANY

        if value.type_ == "null":
            result = Traits.TYPE_NONE

        elif value.type_ == "boolean":
            result = Traits.TYPE_BOOL

        elif value.type_ == "number":
            result = Traits.TYPE_NUMBER

        elif value.type_ == "integer":
            result = Traits.TYPE_INT

        elif value.type_ == "string":
            if value.format_ == "byte":
                result = Traits.TYPE_BYTES
            elif value.format_ == "date":
                result = Traits.TYPE_DATE
            elif value.format_ == "time":
                result = Traits.TYPE_TIME
            elif value.format_ == "date-time":
                result = Traits.TYPE_DATETIME
            elif value.format_ == "uuid":
                result = Traits.TYPE_UUID
            elif value.format_ == "uri":
                result = TypeDef(name="...")
            else:
                result = Traits.TYPE_STR

        elif value.type_ == "array":
            assert isinstance(value.items, SchemaObject)
            item = self.__get_field_type(value.items)

            if value.unique_items:
                result = Traits.create_collection(item)
            else:
                result = Traits.create_sequence(item)

        elif value.type_ == "object":
            result = Traits.create_mapping(Traits.TYPE_STR, Traits.TYPE_ANY)

        elif options := as_sequence(SchemaObject, value.type_):
            result = Traits.create_union(self.__get_field_type(option) for option in options)

        elif value.enum is not None:
            result = Traits.create_literal(value.enum)

        else:
            raise ValueError(value)

        # if value.nullable:
        #     result = Traits.create_optional(result)

        return result
