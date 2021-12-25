__all__ = (
    "JinjaBasedTypeDefCodeGenerator",
)

import typing as t
from pathlib import Path

from dependency_injector.providers import Object

from asynchron.codegen.app import AsyncApiCodeGenerator
from asynchron.codegen.cli import CLIContainer
from asynchron.codegen.generator.jinja.jinja_renderer import JinjaTemplateRenderer
from asynchron.codegen.generator.schema_object_based_type_definition import SchemaObjectBasedPythonModelDefGenerator, SchemaObjectBasedTypeDefGenerator
from asynchron.codegen.info import AsyncApiCodeGeneratorMetaInfo
from asynchron.codegen.spec.base import (
    AsyncAPIObject,
    MessageObject,
    SchemaObject,
)
from asynchron.codegen.spec.type_definition import (
    ClassDef, EnumDef, InlineEnumDef, TypeDef, TypeDefVisitor, TypeImportDef, TypeRef,
)
from asynchron.codegen.spec.visitor.type_def_descendants import TypeDefDescendantsVisitor
from asynchron.codegen.spec.walker.dfs import DFSWalker
from asynchron.strict_typing import as_


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
                        "messages": [
                            message_def
                            for message_def in normalized_message_defs
                            if isinstance(message_def, ClassDef)
                        ],
                        "imports": [
                            import_def
                            for import_def in normalized_message_defs
                            if isinstance(import_def, TypeImportDef)
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
        walking_visitor = TypeDefDescendantsVisitor()
        normalizing_visitor = TypeDefNormalizingVisitor(walking_visitor)

        def get_descendants(value: TypeDef) -> t.Sequence[TypeDef]:
            normalized_value = value.accept_visitor(normalizing_visitor)
            return normalized_value.accept_visitor(walking_visitor)

        walker = DFSWalker(get_descendants)
        visited = set()
        result = []

        for message_def in message_defs:
            for type_def in walker.walk(message_def):
                if type_def not in visited:
                    result.insert(0, type_def)
                    visited.add(type_def)

        return result


class TypeDefNormalizingVisitor(TypeDefVisitor[TypeDef]):
    def __init__(self, inner) -> None:
        self.__inner = inner

    def visit_type_reference(self, obj: TypeRef) -> TypeDef:
        raise NotImplementedError

    def visit_import_def(self, obj: TypeImportDef) -> TypeDef:
        return obj

    def visit_class_def(self, obj: ClassDef) -> TypeDef:
        if import_def := self.__try_replace_with_import(obj.modules):
            return import_def

        else:
            return obj

    def visit_inline_enum_def(self, obj: InlineEnumDef) -> TypeDef:
        if import_def := self.__try_replace_with_import(obj.modules):
            return import_def

        else:
            return obj

    def visit_enum_def(self, obj: EnumDef) -> TypeDef:
        if import_def := self.__try_replace_with_import(obj.modules):
            return import_def

        else:
            return obj

    def __try_replace_with_import(self, modules: t.Sequence[TypeImportDef]) -> t.Optional[TypeImportDef]:
        if not modules:
            return None

        return modules[0]


def main() -> None:
    container = CLIContainer()
    container.config_path.override(Object(Path.home() / "dev/zerlok/dillery/asyncapi.yaml"))

    config = container.config()

    gen = JinjaBasedTypeDefCodeGenerator(...)
    for path, code in gen.generate(config):
        print("".join(code))


if __name__ == "__main__":
    main()
