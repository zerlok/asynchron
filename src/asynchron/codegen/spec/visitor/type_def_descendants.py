__all__ = (
    "TypeDefDescendantsVisitor",
)

import typing as t

from asynchron.codegen.spec.type_definition import (
    ClassDef,
    EnumDef,
    InlineEnumDef,
    TypeDef,
    TypeDefVisitor,
    TypeImportDef, TypeRef,
)


class TypeDefDescendantsVisitor(TypeDefVisitor[t.Sequence[TypeDef]]):

    def visit_type_reference(self, obj: TypeRef) -> t.Sequence[TypeDef]:
        return ()

    def visit_import_def(self, obj: TypeImportDef) -> t.Sequence[TypeDef]:
        return ()

    def visit_class_def(self, obj: ClassDef) -> t.Sequence[TypeDef]:
        return [
            *obj.type_parameters,
            *obj.bases,
            *obj.modules,
            *(
                field.of_type
                for field in obj.fields
            ),
        ]

    def visit_inline_enum_def(self, obj: InlineEnumDef) -> t.Sequence[TypeDef]:
        return [
            *obj.bases,
            *obj.modules,
        ]

    def visit_enum_def(self, obj: EnumDef) -> t.Sequence[TypeDef]:
        return [
            *obj.bases,
            *obj.modules,
        ]
