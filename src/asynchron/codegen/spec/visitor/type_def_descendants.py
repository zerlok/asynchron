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
    ModuleDef, TypeRef,
)
from asynchron.strict_typing import to_sequence


class TypeDefDescendantsVisitor(TypeDefVisitor[t.Sequence[TypeDef]]):

    def visit_type_reference(self, obj: TypeRef) -> t.Sequence[TypeDef]:
        return ()

    def visit_module_def(self, obj: ModuleDef) -> t.Sequence[TypeDef]:
        return ()

    def visit_class_def(self, obj: ClassDef) -> t.Sequence[TypeDef]:
        return [
            *obj.type_parameters,
            *obj.bases,
            *to_sequence(obj.module),
            *(
                field.of_type
                for field in obj.fields
            ),
        ]

    def visit_inline_enum_def(self, obj: InlineEnumDef) -> t.Sequence[TypeDef]:
        return [
            *obj.bases,
            *to_sequence(obj.module),
        ]

    def visit_enum_def(self, obj: EnumDef) -> t.Sequence[TypeDef]:
        return [
            *obj.bases,
            *to_sequence(obj.module),
        ]
