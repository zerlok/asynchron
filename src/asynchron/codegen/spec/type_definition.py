__all__ = (
    "TypeDef",
    "Expr",
    "TypeRef",
    "TypeImportDef",
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

# from pydantic.dataclasses import dataclass
# from pydantic.fields import Field

T = t.TypeVar("T")
T_co = t.TypeVar("T_co", covariant=True)


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
class TypeImportDef(TypeDef):
    module_path: t.Sequence[str]

    def accept_visitor(self, visitor: "TypeDefVisitor[T]") -> T:
        return visitor.visit_import_def(self)


@dataclass(frozen=True)
class TypeRef(TypeDef):
    schema: SchemaObject

    def __hash__(self) -> int:
        return super().__hash__()

    def accept_visitor(self, visitor: "TypeDefVisitor[T]") -> T:
        return visitor.visit_type_reference(self)


@dataclass(frozen=True)
class ClassDef(TypeDef):
    @dataclass(frozen=True)
    class FieldDef:
        name: str
        of_type: TypeDef
        info: FieldInfo

    type_parameters: t.Sequence[TypeDef] = Field(default_factory=tuple)
    modules: t.Sequence[TypeImportDef] = Field(default_factory=tuple)
    bases: t.Sequence[TypeDef] = Field(default_factory=tuple)
    fields: t.Sequence[FieldDef] = Field(default_factory=tuple)
    description: t.Optional[str] = Field(default=None)

    def accept_visitor(self, visitor: "TypeDefVisitor[T]") -> T:
        return visitor.visit_class_def(self)


@dataclass(frozen=True)
class InlineEnumDef(TypeDef):
    literals: t.Sequence[Expr]
    modules: t.Sequence[TypeImportDef] = Field(default_factory=tuple)
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
    modules: t.Sequence[TypeImportDef] = Field(default_factory=tuple)
    bases: t.Sequence[TypeDef] = Field(default_factory=tuple)
    description: t.Optional[str] = Field(default=None)

    def accept_visitor(self, visitor: "TypeDefVisitor[T]") -> T:
        return visitor.visit_enum_def(self)


class TypeDefVisitor(t.Generic[T_co], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def visit_type_reference(self, obj: TypeRef) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_import_def(self, obj: TypeImportDef) -> T_co:
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
