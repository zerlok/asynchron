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
from asynchron.strict_typing import make_sequence_of_not_none


class TypeDefDescendantsVisitor(TypeDefVisitor[t.Sequence[TypeDef]]):

    def visit_type_reference(self, obj: TypeRef) -> t.Sequence[TypeDef]:
        return ()

    def visit_module_def(self, obj: ModuleDef) -> t.Sequence[TypeDef]:
        return ()

    def visit_class_def(self, obj: ClassDef) -> t.Sequence[TypeDef]:
        return make_sequence_of_not_none(
            *obj.type_parameters,
            *obj.bases,
            *(
                field.of_type
                for field in obj.fields
            ),
            obj.module,
        )

    def visit_inline_enum_def(self, obj: InlineEnumDef) -> t.Sequence[TypeDef]:
        return make_sequence_of_not_none(
            *obj.bases,
            obj.module,
        )

    def visit_enum_def(self, obj: EnumDef) -> t.Sequence[TypeDef]:
        return make_sequence_of_not_none(
            *obj.bases,
            obj.module,
        )
