__all__ = (
    "TypeDef",
    "Expr",
    "TypeRef",
    "ModuleDef",
    "ClassDef",
    "InlineEnumDef",
    "EnumDef",
    "TypeDefVisitor",
)

import abc
import typing as t
from dataclasses import dataclass, field as Field

from pydantic.fields import FieldInfo

from asynchron.codegen.spec.base import SchemaObject
from asynchron.strict_typing import T, T_co


@dataclass(frozen=True)
class TypeDef:
    path: t.Sequence[str]

    def accept_visitor(self, visitor: "TypeDefVisitor[T]") -> T:
        raise NotImplementedError


@dataclass(frozen=True)
class Expr:
    value: str
    uses: t.Collection[TypeDef]


@dataclass(frozen=True)
class TypeRef(TypeDef):
    schema: SchemaObject

    def __hash__(self) -> int:
        return super().__hash__()

    def accept_visitor(self, visitor: "TypeDefVisitor[T]") -> T:
        return visitor.visit_type_reference(self)


@dataclass(frozen=True)
class ModuleDef(TypeDef):
    alias: t.Optional[str] = None

    def accept_visitor(self, visitor: "TypeDefVisitor[T]") -> T:
        return visitor.visit_module_def(self)


@dataclass(frozen=True)
class ClassDef(TypeDef):
    @dataclass(frozen=True)
    class FieldDef:
        name: str
        of_type: TypeDef
        info: FieldInfo

    module: t.Optional[ModuleDef] = Field(default=None)
    type_parameters: t.Sequence[TypeDef] = Field(default_factory=tuple)
    bases: t.Sequence[TypeDef] = Field(default_factory=tuple)
    fields: t.Sequence[FieldDef] = Field(default_factory=tuple)
    description: t.Optional[str] = Field(default=None)

    def accept_visitor(self, visitor: "TypeDefVisitor[T]") -> T:
        return visitor.visit_class_def(self)


@dataclass(frozen=True)
class InlineEnumDef(TypeDef):
    literals: t.Sequence[Expr]
    module: t.Optional[ModuleDef] = Field(default=None)
    bases: t.Sequence[TypeDef] = Field(default_factory=tuple)

    def accept_visitor(self, visitor: "TypeDefVisitor[T]") -> T:
        return visitor.visit_inline_enum_def(self)


@dataclass(frozen=True)
class EnumDef(TypeDef):
    @dataclass(frozen=True)
    class LiteralDef:
        name: str
        value: Expr

    literals: t.Sequence[LiteralDef]
    module: t.Optional[ModuleDef] = Field(default=None)
    bases: t.Sequence[TypeDef] = Field(default_factory=tuple)
    description: t.Optional[str] = Field(default=None)

    def accept_visitor(self, visitor: "TypeDefVisitor[T]") -> T:
        return visitor.visit_enum_def(self)


class TypeDefVisitor(t.Generic[T_co], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def visit_type_reference(self, obj: TypeRef) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_module_def(self, obj: ModuleDef) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_class_def(self, obj: ClassDef) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_inline_enum_def(self, obj: InlineEnumDef) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_enum_def(self, obj: EnumDef) -> T_co:
        raise NotImplementedError
