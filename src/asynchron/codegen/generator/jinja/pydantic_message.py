__all__ = (
    "JinjaBasedTypeDefCodeGenerator",
)

import itertools as it
import typing as t
from dataclasses import replace
from pathlib import Path

from dependency_injector.providers import Object

from asynchron.codegen.app import AsyncApiCodeGenerator
from asynchron.codegen.cli import CLIContainer
from asynchron.codegen.generator.jinja.jinja_renderer import JinjaTemplateRenderer
from asynchron.codegen.generator.schema_object_based_type_definition import (
    SchemaObjectBasedPythonModelDefGenerator,
    SchemaObjectBasedTypeDefGenerator,
)
from asynchron.codegen.info import AsyncApiCodeGeneratorMetaInfo
from asynchron.codegen.spec.base import (
    AsyncAPIObject,
    MessageObject,
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
from asynchron.codegen.spec.walker.dfs import DFSWalker
from asynchron.strict_typing import as_


# TODO: cleanup
class JinjaBasedTypeDefCodeGenerator(AsyncApiCodeGenerator):
    __JINJA_TEMPLATES_DIR: t.Final[Path] = Path(__file__).parent / "templates"

    def __init__(
            self,
            meta: AsyncApiCodeGeneratorMetaInfo,
            type_def_generator: t.Optional[SchemaObjectBasedTypeDefGenerator] = None,
            renderer: t.Optional[JinjaTemplateRenderer] = None,
    ) -> None:
        self.__meta = meta
        self.__type_def_generator = type_def_generator or SchemaObjectBasedPythonModelDefGenerator()
        self.__renderer = renderer or JinjaTemplateRenderer.from_template_root_dir(self.__JINJA_TEMPLATES_DIR)

    def generate(self, config: AsyncAPIObject) -> t.Iterable[t.Tuple[Path, t.Iterable[str]]]:
        message_defs: t.List[TypeDef] = []
        for channel_name, channel, operation in config.iter_channel_operations():
            # TODO: support message sequence
            message = as_(MessageObject, operation.message)
            if message is None:
                continue

            payload = as_(SchemaObject, message.payload)
            if payload is None:
                continue

            type_def = self.__type_def_generator.get_type_def_from_json_schema(payload)
            if type_def is not None:
                message_defs.append(type_def)

        normalized_message_defs = self.__normalized_message_def_order_by_dependencies(message_defs)
        return (
            (
                Path("message.py"),
                self.__renderer.render(
                    name="message",
                    context={
                        "meta": self.__meta,
                        "classes": [
                            message_def
                            for message_def in normalized_message_defs
                            if isinstance(message_def, ClassDef)
                        ],
                        "imports": [
                            import_def
                            for import_def in normalized_message_defs
                            if isinstance(import_def, ModuleDef)
                        ],
                        "module": ...,
                        "app": ...,
                    },
                ),
            ),
        )

    def __normalized_message_def_order_by_dependencies(
            self,
            message_defs: t.Sequence[TypeDef],
    ) -> t.Sequence[TypeDef]:
        walking_visitor = TypeDefNestingVisitor(
            TypeDefDescendantsVisitor(),
            ImportedClassDefOmittingVisitor(),
        )

        @DFSWalker
        def walker(value: TypeDef) -> t.Sequence[TypeDef]:
            return value.accept_visitor(walking_visitor)

        normalizer = TypeDefTransformingVisitor(
            TypeDefNestingVisitor(
                SingleBaseInheritanceClassDefReplacingVisitor(),
            ),
        )

        visited = set()
        result = []

        for message_def in message_defs:
            for type_def in walker.walk(message_def.accept_visitor(normalizer)):
                if type_def not in visited:
                    print(type_def)
                    result.insert(0, type_def)
                    visited.add(type_def)

        return result


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

    #
    # def __get_first_transformed(self, value: TypeDef) -> TypeDef:
    #     return value.accept_visitor(self.__transformer)[0]
    #
    # def __get_optional_first_transformed(self, value: t.Optional[TypeDef]) -> t.Optional[TypeDef]:
    #     if value is None:
    #         return None
    #
    #     result = value.accept_visitor(self.__transformer)
    #     if not result:
    #         return None
    #
    #     return result[0]
    #
    # def __chain_transformed(self, values: t.Sequence[TypeDef]) -> t.Sequence[TypeDef]:
    #     return tuple(it.chain.from_iterable(value.accept_visitor(self.__transformer) for value in values))


class TypeDefSequentialVisitor(TypeDefVisitor[TypeDef]):
    def __init__(self, *visitors: TypeDefVisitor[TypeDef]) -> None:
        self.__visitors = visitors

    def visit_type_reference(self, obj: TypeRef) -> TypeDef:
        return self.__visit_sequentially(obj)

    def visit_module_def(self, obj: ModuleDef) -> TypeDef:
        return self.__visit_sequentially(obj)

    def visit_class_def(self, obj: ClassDef) -> TypeDef:
        return self.__visit_sequentially(obj)

    def visit_inline_enum_def(self, obj: InlineEnumDef) -> TypeDef:
        return self.__visit_sequentially(obj)

    def visit_enum_def(self, obj: EnumDef) -> TypeDef:
        return self.__visit_sequentially(obj)

    def __visit_sequentially(self, obj: TypeDef) -> TypeDef:
        result = obj

        for visitor in self.__visitors:
            result = result.accept_visitor(visitor)

        return result


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
        result = (obj,)

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
        return (obj,)

    def visit_enum_def(self, obj: EnumDef) -> t.Sequence[TypeDef]:
        return (obj,)


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


def main() -> None:
    container = CLIContainer()
    container.config_path.override(Object(Path.home() / "dev/zerlok/dillery/asyncapi.yaml"))

    config = container.config()

    gen = JinjaBasedTypeDefCodeGenerator(...)
    for path, code in gen.generate(config):
        print("".join(code))


if __name__ == "__main__":
    main()
