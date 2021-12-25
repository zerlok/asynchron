__all__ = (
    "SchemaObjectBasedTypeDefGenerator",
    "SchemaObjectBasedPythonTypeDefGenerator",
    "SchemaObjectBasedPythonModelDefGenerator",
)

import abc
import typing as t
from dataclasses import replace

from pydantic.fields import FieldInfo

from asynchron.codegen.spec.base import SchemaObject
from asynchron.codegen.spec.type_definition import (
    ClassDef,
    EnumDef,
    Expr,
    InlineEnumDef,
    TypeDef,
    TypeImportDef,
    TypeRef,
)
from asynchron.strict_typing import as_, as_mapping, as_sequence, raise_not_exhaustive


class SchemaObjectBasedTypeDefGenerator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_type_def_from_json_schema(self, schema: SchemaObject) -> t.Optional[TypeDef]:
        raise NotImplementedError


class SchemaObjectBasedPythonTypeDefGenerator(SchemaObjectBasedTypeDefGenerator):
    __SCALAR_PYTHON_TYPES_BY_JSON_TYPE_AND_FORMAT: t.Final[
        t.Mapping[t.Optional[str], t.Mapping[t.Optional[str], t.Optional[TypeDef]]]
    ] = {
        None: None,
        "null": {None: ClassDef(("None",), modules=(TypeImportDef((), ("builtins",), ),), )},
        "boolean": {None: ClassDef(("bool",), modules=(TypeImportDef((), ("builtins",), ),), )},
        "integer": {None: ClassDef(("int",), modules=(TypeImportDef((), ("builtins",), ),), )},
        "number": {
            None: ClassDef(
                path=(),
                type_parameters=(ClassDef(("int",), modules=(TypeImportDef((), ("builtins",), ),), ),
                                 ClassDef(("float",), modules=(TypeImportDef((), ("builtins",), ),), ),),
                bases=(ClassDef(("typing", "Union"), modules=(TypeImportDef((), ("typing",), ),)),),
            ),
        },
        "string": {
            None: ClassDef(("str",), modules=(TypeImportDef((), ("builtins",), ),), ),
            "byte": ClassDef(("bytes",), modules=(TypeImportDef((), ("builtins",), ),), ),
            "date": ClassDef(("datetime", "date",), modules=(TypeImportDef((), ("datetime", "datetime"), ),)),
            "time": ClassDef(("datetime", "time",), modules=(TypeImportDef((), ("datetime", "datetime"), ),)),
            "date-time": ClassDef(("datetime", "datetime",), modules=(TypeImportDef((), ("datetime", "datetime"), ),)),
            "uuid": ClassDef(("uuid", "UUID",), modules=(TypeImportDef((), ("uuid",)),), ),
            "uri": ClassDef(("str",), modules=(TypeImportDef((), ("builtins",), ),), ),
        },
    }

    def get_type_def_from_json_schema(self, schema: SchemaObject) -> t.Optional[TypeDef]:
        scalar_formats = self.__SCALAR_PYTHON_TYPES_BY_JSON_TYPE_AND_FORMAT.get(schema.type_) or {}
        if scalar_type_def := scalar_formats.get(schema.format_):
            return scalar_type_def

        return None


class SchemaObjectBasedPythonModelDefGenerator(SchemaObjectBasedTypeDefGenerator):
    __DEFAULT_SCALAR_GENERATOR: t.Final[SchemaObjectBasedTypeDefGenerator] = SchemaObjectBasedPythonTypeDefGenerator()
    __DEFAULT_ANY: t.Final[TypeDef] = ClassDef(("typing", "Any",), modules=(TypeImportDef((), ("typing",), ),))
    __DEFAULT_OBJECT: t.Final[TypeDef] = ClassDef(("pydantic", "BaseModel",),
                                                  modules=(TypeImportDef((), ("pydantic",), ),))
    __DEFAULT_ARRAY: t.Final[TypeDef] = ClassDef(("typing", "Sequence",), modules=(TypeImportDef((), ("typing",), ),))
    __DEFAULT_SET: t.Final[TypeDef] = ClassDef(("typing", "Collection",), modules=(TypeImportDef((), ("typing",), ),))
    __DEFAULT_OPTIONAL: t.Final[TypeDef] = ClassDef(("typing", "Optional",),
                                                    modules=(TypeImportDef((), ("typing",), ),))
    __DEFAULT_UNION: t.Final[TypeDef] = ClassDef(("typing", "Union",), modules=(TypeImportDef((), ("typing",), ),))
    __DEFAULT_ENUM: t.Final[TypeDef] = ClassDef(("enum", "Enum",), modules=(TypeImportDef((), ("enum",), ),))
    __DEFAULT_INLINE_ENUM: t.Final[TypeDef] = ClassDef(("typing", "Literal",),
                                                       modules=(TypeImportDef((), ("typing",), ),))

    def __init__(
            self,
            scalar_generator: t.Optional[SchemaObjectBasedTypeDefGenerator] = None,
            any_class_def: t.Optional[TypeDef] = None,
            object_class_def: t.Optional[TypeDef] = None,
            array_class_def: t.Optional[TypeDef] = None,
            set_class_def: t.Optional[TypeDef] = None,
            optional_class_def: t.Optional[TypeDef] = None,
            union_class_def: t.Optional[TypeDef] = None,
            enum_class_def: t.Optional[TypeDef] = None,
            inline_enum_class_def: t.Optional[TypeDef] = None,
    ) -> None:
        self.__scalar_generator = scalar_generator or self.__DEFAULT_SCALAR_GENERATOR
        self.__any_class_def = any_class_def or self.__DEFAULT_ANY
        self.__object_class_def = object_class_def or self.__DEFAULT_OBJECT
        self.__array_class_def = array_class_def or self.__DEFAULT_ARRAY
        self.__set_class_def = set_class_def or self.__DEFAULT_SET
        self.__optional_class_def = optional_class_def or self.__DEFAULT_OPTIONAL
        self.__union_class_def = union_class_def or self.__DEFAULT_UNION
        self.__enum_class_def = enum_class_def or self.__DEFAULT_ENUM
        self.__inline_enum_class_def = inline_enum_class_def or self.__DEFAULT_INLINE_ENUM

    def get_type_def_from_json_schema(self, schema: SchemaObject) -> t.Optional[TypeDef]:
        root_ref = self.__get_type_ref((), schema)

        found_defs_by_refs: t.Dict[TypeRef, TypeDef] = {}

        queue: t.List[TypeRef] = [root_ref]
        while queue:
            item = queue.pop(0)
            type_def = found_defs_by_refs[item] = self.__get_for_schema_with_references(item.path, item.schema)

            for used_type_def in self.__iter_used_type_defs(type_def):
                if ref := as_(TypeRef, used_type_def):
                    queue.append(ref)

        root_def = found_defs_by_refs[root_ref]
        result_def = self.__resolve_references(root_def, found_defs_by_refs)

        return result_def

    def __get_name(self, schema: SchemaObject) -> str:
        if title := schema.title:
            return title

        raise ValueError()

    def __get_path(self, parent: t.Sequence[str], schema: SchemaObject) -> t.Sequence[str]:
        return *parent, self.__get_name(schema)

    def __get_type_ref(self, parent: t.Sequence[str], schema: SchemaObject) -> TypeRef:
        return TypeRef(self.__get_path(parent, schema), schema)

    def __get_optional(self, type_def: TypeDef) -> TypeDef:
        return ClassDef((), type_parameters=(type_def,), bases=(self.__optional_class_def,))

    def __get_union(
            self,
            root_path: t.Sequence[str],
            name: str,
            part_schemas: t.Sequence[SchemaObject],
    ) -> TypeDef:
        return ClassDef(
            path=(*root_path, name),
            type_parameters=tuple(
                self.__get_type_ref(root_path, part_schema)
                for part_schema in part_schemas
            ),
            bases=(self.__union_class_def,),
        )

    def __get_field_def(
            self,
            root_path: t.Sequence[str],
            name: str,
            schema: SchemaObject,
            is_optional: bool,
    ) -> ClassDef.FieldDef:
        field_type_def = self.__get_type_ref(root_path, schema)
        if is_optional:
            field_type_def = self.__get_optional(field_type_def)

        return ClassDef.FieldDef(
            name=name,
            of_type=field_type_def,
            info=FieldInfo(
                default=schema.default,
                alias=name,
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

    def __get_for_schema_with_references(self, path: t.Sequence[str], schema: SchemaObject) -> TypeDef:
        bases: t.List[TypeDef] = []

        if scalar_type_def := self.__scalar_generator.get_type_def_from_json_schema(schema):
            bases.append(scalar_type_def)

        if part_schemas := as_sequence(SchemaObject, schema.all_of):
            bases.extend(
                self.__get_type_ref(path, part_schema)
                for part_schema in part_schemas
            )

        if part_schemas := as_sequence(SchemaObject, schema.any_of):
            bases.append(self.__get_union(path, "options", part_schemas))

        if part_schemas := as_sequence(SchemaObject, schema.one_of):
            bases.append(self.__get_union(path, "alternatives", part_schemas))

        if properties := as_mapping(str, SchemaObject, schema.properties):
            required_field_names = set(schema.required or ())
            bases.append(ClassDef(
                path=(*path, "object"),
                bases=(self.__object_class_def,),
                fields=tuple(
                    self.__get_field_def(path, field_name, field_schema, field_name not in required_field_names)
                    for field_name, field_schema in properties.items()
                ),
            ))

        elif schema.type_ == "array":
            if element_schema := as_(SchemaObject, schema.items):
                element_def = self.__get_type_ref(path, element_schema)

            elif element_schemas := as_sequence(SchemaObject, schema.items):
                element_def = self.__get_union(path, "items", element_schemas)

            else:
                element_def = self.__any_class_def

            bases.append(ClassDef(
                path=(*path, "array"),
                type_parameters=(element_def,),
                bases=(self.__array_class_def,) if not schema.unique_items else (self.__set_class_def,),
            ))

        elif literal_schemas := as_sequence(SchemaObject, schema.enum):
            bases.append(EnumDef(
                path=(*path, "enum"),
                literals=tuple(
                    EnumDef.LiteralDef(
                        name=self.__get_name(literal_schema),
                        value=Expr("enum.auto()", uses=(ClassDef(("enum", "auto",)),)),
                    )
                    for literal_schema in literal_schemas
                ),
                bases=(self.__enum_class_def,),
            ))

        elif inline_enum_literals := schema.enum:
            bases.append(InlineEnumDef(
                path=(*path, "enum"),
                literals=tuple(
                    Expr(repr(literal), ())
                    for literal in inline_enum_literals
                ),
                bases=(self.__inline_enum_class_def,),
            ))

        return ClassDef(
            path=path,
            bases=tuple(bases),
        )

    def __iter_used_type_defs(self, root: TypeDef) -> t.Iterable[TypeDef]:
        queue: t.List[TypeDef] = [root]

        while queue:
            type_def = queue.pop(0)

            if class_def := as_(ClassDef, type_def):
                queue.extend(class_def.type_parameters)
                queue.extend(class_def.bases)
                queue.extend(
                    field_def.of_type
                    for field_def in class_def.fields
                )

            elif inline_enum_def := as_(InlineEnumDef, type_def):
                queue.extend(inline_enum_def.bases)

            elif enum_def := as_(EnumDef, type_def):
                queue.extend(enum_def.bases)

            elif as_(TypeRef, type_def):
                pass

            else:
                raise_not_exhaustive(type(type_def), type_def)

            yield type_def

    def __resolve_references(
            self,
            type_def: TypeDef,
            references: t.Mapping[TypeRef, TypeDef],
    ) -> TypeDef:
        if class_def := as_(ClassDef, type_def):
            if not class_def.type_parameters and len(class_def.bases) == 1 and not class_def.fields:
                class_def = class_def.bases[0]

            elif len(class_def.bases) == 1 and not class_def.fields:
                class_def = replace(class_def, path=self.__resolve_references(class_def.bases[0], references).path)

            return replace(
                class_def,
                type_parameters=tuple(
                    self.__resolve_references(type_parameter, references)
                    for type_parameter in class_def.type_parameters
                ),
                bases=tuple(
                    self.__resolve_references(base, references)
                    for base in class_def.bases
                ),
                fields=tuple(
                    replace(
                        field_def,
                        of_type=self.__resolve_references(field_def.of_type, references),
                    )
                    for field_def in class_def.fields
                ),
            )

        elif inline_enum_def := as_(InlineEnumDef, type_def):
            return replace(
                inline_enum_def,
                bases=tuple(
                    self.__resolve_references(base, references)
                    for base in inline_enum_def.bases
                ),
            )

        elif enum_def := as_(EnumDef, type_def):
            return replace(
                enum_def,
                bases=tuple(
                    self.__resolve_references(base, references)
                    for base in enum_def.bases
                ),
            )

        elif type_ref := as_(TypeRef, type_def):
            return self.__resolve_references(references[type_ref], references)

        else:
            raise_not_exhaustive(type(type_def), type_def)
