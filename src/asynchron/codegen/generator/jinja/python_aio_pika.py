__all__ = (
    "JinjaBasedPythonAioPikaCodeGenerator",
)

import itertools as it
import typing as t
from dataclasses import dataclass, replace
from pathlib import Path

import stringcase  # type: ignore

from asynchron.codegen.app import AsyncApiCodeGenerator
from asynchron.codegen.generator.jinja.jinja_renderer import JinjaTemplateRenderer
from asynchron.codegen.generator.schema_object_based_type_definition import (
    SchemaObjectBasedPythonModelDefGenerator,
    SchemaObjectBasedTypeDefGenerator,
)
from asynchron.codegen.info import AsyncApiCodeGeneratorMetaInfo
from asynchron.codegen.spec.base import (
    AMQPBindingTrait,
    AsyncAPIObject,
    ChannelBindingsObject, ChannelItemObject,
    MessageObject,
    OperationBindingsObject, OperationObject,
    SchemaObject,
)
from asynchron.codegen.spec.type_definition import (
    ClassDef,
    EnumDef,
    InlineEnumDef,
    ModuleDef,
    TypeDef,
    TypeDefVisitor,
    TypeRef,
)
from asynchron.codegen.spec.visitor.type_def_descendants import TypeDefDescendantsVisitor
from asynchron.codegen.spec.walker.dfs import DFSPPostOrderingWalker
from asynchron.strict_typing import as_

K = t.TypeVar("K", bound=t.Hashable)
V = t.TypeVar("V")
T = t.TypeVar("T")


@dataclass(frozen=True)
class ConsumerDef:
    name: str
    description: t.Optional[str]
    message: TypeDef
    exchange_name: str
    queue_name: t.Optional[str]
    binding_keys: t.Collection[str]


@dataclass(frozen=True)
class PublisherDef:
    name: str
    description: t.Optional[str]
    message: TypeDef
    exchange_name: str
    routing_key: str
    is_mandatory: t.Optional[bool]


@dataclass(frozen=True)
class AppDef:
    name: str
    description: t.Optional[str]
    modules: t.Collection[ModuleDef]
    consumers: t.Collection[ConsumerDef]
    publishers: t.Collection[PublisherDef]
    type_defs: t.Sequence[TypeDef]


class JinjaBasedPythonAioPikaCodeGenerator(AsyncApiCodeGenerator):
    __JINJA_TEMPLATES_DIR: t.Final[Path] = Path(__file__).parent / "templates"

    def __init__(
            self,
            meta: AsyncApiCodeGeneratorMetaInfo,
            message_def_generator: t.Optional[SchemaObjectBasedTypeDefGenerator] = None,
            renderer: t.Optional[JinjaTemplateRenderer] = None,
    ) -> None:
        self.__meta = meta
        self.__message_def_generator = message_def_generator or SchemaObjectBasedPythonModelDefGenerator()
        self.__renderer = renderer or JinjaTemplateRenderer.from_template_root_dir(self.__JINJA_TEMPLATES_DIR)

    def generate(self, config: AsyncAPIObject) -> t.Iterable[t.Tuple[Path, t.Iterable[str]]]:
        channel_messages: t.Dict[str, TypeDef] = dict(self.__iter_message_defs(config))
        app_consumers = list(self.__iter_amqp_consumer_defs(config, channel_messages))
        app_publishers = list(self.__iter_amqp_publisher_defs(config, channel_messages))
        app_modules = list(self.__iter_app_modules(config))
        app_type_defs = list(self.__get_app_type_defs_ordered_by_dependency(channel_messages.values()))

        app = AppDef(
            name=config.info.title,
            description=config.info.description,
            modules=app_modules,
            consumers=app_consumers,
            publishers=app_publishers,
            type_defs=app_type_defs,
        )

        for module, render_context in self.__iter_rendering_modules(app):
            module_path = Path(*module.path[:-1], f"{module.path[-1]}.py")

            stream = self.__renderer.render(
                name=module.path[-1],
                context=render_context,
            )

            yield module_path, stream

    def __iter_app_modules(
            self,
            config: AsyncAPIObject,
    ) -> t.Iterable[ModuleDef]:
        return (
            ModuleDef(
                path=("__init__",),
            ),
            ModuleDef(
                path=("consumer",),
            ),
            ModuleDef(
                path=("publisher",),
            ),
            ModuleDef(
                path=("message",),
            ),
        )

    def __iter_message_defs(
            self,
            config: AsyncAPIObject,
    ) -> t.Iterable[t.Tuple[str, TypeDef]]:
        for channel_name, channel, operation in config.iter_channel_operations():
            # TODO: support message sequence
            message = as_(MessageObject, operation.message)
            if message is None:
                continue

            payload = as_(SchemaObject, message.payload)
            if payload is None:
                continue

            message_def = self.__message_def_generator.get_type_def_from_json_schema(payload)
            if message_def is None:
                continue

            yield channel_name.replace("/", "_"), message_def

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

            yield channel_name.replace("/", "_"), channel, operation, amqp_channel_bindings, amqp_operation_bindings

    def __iter_amqp_consumer_defs(
            self,
            config: AsyncAPIObject,
            messages: t.Mapping[str, TypeDef],
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
                name=channel_name,
                description=channel.description,
                exchange_name=exchange.name,
                queue_name=queue.name,
                binding_keys=binding_keys,
                message=channel_message,
            )

    def __iter_amqp_publisher_defs(
            self,
            config: AsyncAPIObject,
            messages: t.Mapping[str, TypeDef],
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
                name=channel_name,
                description=channel.description,
                exchange_name=exchange.name,
                routing_key=routing_key,
                is_mandatory=operation_bindings.mandatory,
                message=channel_message,
            )

    def __get_app_type_defs_ordered_by_dependency(
            self,
            message_defs: t.Collection[TypeDef],
    ) -> t.Sequence[TypeDef]:
        type_def_walking_visitor = TypeDefNestingVisitor(
            TypeDefDescendantsVisitor(),
            ImportedClassDefOmittingVisitor(),
        )

        @DFSPPostOrderingWalker
        def walker(value: TypeDef) -> t.Sequence[TypeDef]:
            return value.accept_visitor(type_def_walking_visitor)

        type_def_normalizer = TypeDefSimplifier()

        visited: t.Set[TypeDef] = set()
        result: t.List[TypeDef] = []

        for message_def in message_defs:
            for normalized_message_def in walker.walk(message_def.accept_visitor(type_def_normalizer)):
                if normalized_message_def not in visited:
                    visited.add(normalized_message_def)
                    result.append(normalized_message_def)

        return result

    def __iter_module_defs(self, values: t.Iterable[TypeDef]) -> t.Iterable[ModuleDef]:
        for value in values:
            if module_def := as_(ModuleDef, value):
                yield module_def

    def __iter_class_defs(self, values: t.Iterable[TypeDef]) -> t.Iterable[ClassDef]:
        for value in values:
            if class_def := as_(ClassDef, value):
                yield class_def

    def __iter_rendering_modules(self, app: AppDef) -> t.Iterable[t.Tuple[ModuleDef, t.Mapping[str, object]]]:
        base_context = {
            "app": app,
            "meta": self.__meta,
        }

        settings: t.Collection[t.Tuple[ModuleDef, t.Mapping[str, object]]] = [
            (
                ModuleDef(
                    path=("__init__",),
                ),
                {},
            ),
            (
                ModuleDef(
                    path=("consumer",),
                ),
                {},
            ),
            (
                ModuleDef(
                    path=("publisher",),
                ),
                {},
            ),
            (
                ModuleDef(
                    path=("message",),
                ),
                {
                    "imports": list(self.__iter_module_defs(app.type_defs)),
                    "classes": list(self.__iter_class_defs(app.type_defs)),
                    "is_inline_enum_def": self.__is_inline_enum_def,
                },
            ),
        ]

        for module, context in settings:
            yield module, {
                **base_context,
                "module": module,
                **context,
            }

    def __is_inline_enum_def(self, value: object) -> bool:
        return isinstance(value, InlineEnumDef)


class TypeDefTransformingVisitor(TypeDefVisitor[TypeDef]):
    def __init__(
            self,
            transformer: TypeDefVisitor[t.Sequence[TypeDef]],
    ) -> None:
        self.__transformer = transformer

    def visit_type_reference(self, obj: TypeRef) -> TypeDef:
        return obj

    def visit_module_def(self, obj: ModuleDef) -> TypeDef:
        return obj

    def visit_class_def(self, obj: ClassDef) -> TypeDef:
        return replace(
            obj,
            module=self.__get_optional_first_transformed(obj.module),
            type_parameters=self.__chain_transformed(obj.type_parameters),
            bases=self.__chain_transformed(obj.bases),
            fields=tuple(
                replace(field, of_type=self.__get_first_transformed(field.of_type))
                for field in obj.fields
            ),
        )

    def visit_inline_enum_def(self, obj: InlineEnumDef) -> TypeDef:
        return replace(
            obj,
            module=self.__get_optional_first_transformed(obj.module),
            bases=self.__chain_transformed(obj.bases),
        )

    def visit_enum_def(self, obj: EnumDef) -> TypeDef:
        return replace(
            obj,
            module=self.__get_optional_first_transformed(obj.module),
            bases=self.__chain_transformed(obj.bases),
        )

    def __get_first_transformed(self, value: TypeDef) -> TypeDef:
        return value.accept_visitor(self).accept_visitor(self.__transformer)[0]

    def __get_optional_first_transformed(self, value: t.Optional[TypeDef]) -> t.Optional[TypeDef]:
        if value is None:
            return None

        result = value.accept_visitor(self).accept_visitor(self.__transformer)
        if not result:
            return None

        return result[0]

    def __chain_transformed(self, values: t.Sequence[TypeDef]) -> t.Sequence[TypeDef]:
        return tuple(it.chain.from_iterable(
            value.accept_visitor(self).accept_visitor(self.__transformer)
            for value in values
        ))


class TypeDefNestingVisitor(TypeDefVisitor[t.Sequence[TypeDef]]):
    def __init__(self, *visitors: TypeDefVisitor[t.Sequence[TypeDef]]) -> None:
        self.__visitors = visitors

    def visit_type_reference(self, obj: TypeRef) -> t.Sequence[TypeDef]:
        return self.__visit_sequentially(obj)

    def visit_module_def(self, obj: ModuleDef) -> t.Sequence[TypeDef]:
        return self.__visit_sequentially(obj)

    def visit_class_def(self, obj: ClassDef) -> t.Sequence[TypeDef]:
        return self.__visit_sequentially(obj)

    def visit_inline_enum_def(self, obj: InlineEnumDef) -> t.Sequence[TypeDef]:
        return self.__visit_sequentially(obj)

    def visit_enum_def(self, obj: EnumDef) -> t.Sequence[TypeDef]:
        return self.__visit_sequentially(obj)

    def __visit_sequentially(self, obj: TypeDef) -> t.Sequence[TypeDef]:
        result: t.Sequence[TypeDef] = (obj,)

        for visitor in self.__visitors:
            result = [
                new_value
                for value in result
                for new_value in value.accept_visitor(visitor)
            ]

        return tuple(result)


class SingleBaseInheritanceClassDefReplacingVisitor(TypeDefVisitor[t.Sequence[TypeDef]]):

    def visit_type_reference(self, obj: TypeRef) -> t.Sequence[TypeDef]:
        return (obj,)

    def visit_module_def(self, obj: ModuleDef) -> t.Sequence[TypeDef]:
        return (obj,)

    def visit_class_def(self, obj: ClassDef) -> t.Sequence[TypeDef]:
        if not obj.type_parameters and len(obj.bases) == 1 and not obj.fields:
            return (obj.bases[0],)

        elif len(obj.bases) == 1 and not obj.fields and isinstance(obj.bases[0], ClassDef):
            c = obj.bases[0]
            return (replace(c, type_parameters=obj.type_parameters),)

        return (obj,)

    def visit_inline_enum_def(self, obj: InlineEnumDef) -> t.Sequence[TypeDef]:
        # if obj.literals and len(obj.bases) == 1 and isinstance(obj.bases[0], ClassDef):
        #     c = obj.bases[0]
        #     return (replace(c, path=c.path, ),)

        return (obj,)

    def visit_enum_def(self, obj: EnumDef) -> t.Sequence[TypeDef]:
        return (obj,)


class TypeDefSimplifier(TypeDefVisitor[TypeDef]):

    def visit_type_reference(self, obj: TypeRef) -> TypeDef:
        return obj

    def visit_module_def(self, obj: ModuleDef) -> TypeDef:
        return obj

    def visit_class_def(self, obj: ClassDef) -> TypeDef:
        if len(obj.bases) == 1 and not obj.fields:
            base = obj.bases[0]

            if isinstance(base, (ClassDef, InlineEnumDef)):
                if not obj.type_parameters:
                    if base.module is None:
                        return replace(base, path=obj.path).accept_visitor(self)

                    else:
                        return base.accept_visitor(self)

                else:
                    return replace(base, type_parameters=obj.type_parameters).accept_visitor(self)

        return replace(obj, type_parameters=tuple(tp.accept_visitor(self) for tp in obj.type_parameters),
                       bases=tuple(base.accept_visitor(self) for base in obj.bases),
                       module=obj.module.accept_visitor(self) if obj.module is not None else None,
                       fields=tuple(replace(field, of_type=field.of_type.accept_visitor(self)) for field in obj.fields),
                       )

    def visit_inline_enum_def(self, obj: InlineEnumDef) -> TypeDef:
        return replace(obj, bases=tuple(base.accept_visitor(self) for base in obj.bases),
                       module=obj.module.accept_visitor(self) if obj.module is not None else None)

    def visit_enum_def(self, obj: EnumDef) -> TypeDef:
        return replace(obj, bases=tuple(base.accept_visitor(self) for base in obj.bases),
                       module=obj.module.accept_visitor(self) if obj.module is not None else None)


class ImportedClassDefOmittingVisitor(TypeDefVisitor[t.Sequence[TypeDef]]):

    def visit_type_reference(self, obj: TypeRef) -> t.Sequence[TypeDef]:
        return (obj,)

    def visit_module_def(self, obj: ModuleDef) -> t.Sequence[TypeDef]:
        return (obj,)

    def visit_class_def(self, obj: ClassDef) -> t.Sequence[TypeDef]:
        if module := obj.module:
            return (*it.chain.from_iterable(tp.accept_visitor(self) for tp in obj.type_parameters), module,)

        return (obj,)

    def visit_inline_enum_def(self, obj: InlineEnumDef) -> t.Sequence[TypeDef]:
        if module := obj.module:
            return (module,)

        return (obj,)

    def visit_enum_def(self, obj: EnumDef) -> t.Sequence[TypeDef]:
        if module := obj.module:
            return (module,)

        return (obj,)
