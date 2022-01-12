__all__ = (
    "SchemaObjectBasedTypeDefGenerator",
    "SchemaObjectBasedPythonTypeDefGenerator",
    "SchemaObjectBasedPythonModelDefGenerator",
)

import abc
import typing as t
from dataclasses import replace

from pydantic.fields import FieldInfo

from asynchron.codegen.spec.base import SchemaObject, SchemaObjectType
from asynchron.codegen.spec.type_definition import ClassDef, EnumDef, Expr, InlineEnumDef, ModuleDef, TypeDef, TypeRef
from asynchron.strict_typing import as_, as_mapping, as_sequence, make_sequence_of_not_none, raise_not_exhaustive


class SchemaObjectBasedTypeDefGenerator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_type_def_from_json_schema(self, schema: SchemaObject) -> t.Optional[TypeDef]:
        raise NotImplementedError


class SchemaObjectBasedPythonTypeDefGenerator(SchemaObjectBasedTypeDefGenerator):
    __BUILTINS_MODULE: t.Final[ModuleDef] = ModuleDef(("builtins",))
    __TYPING_MODULE: t.Final[ModuleDef] = ModuleDef(("typing",))
    __DATETIME_MODULE: t.Final[ModuleDef] = ModuleDef(("datetime",))
    __UUID_MODULE: t.Final[ModuleDef] = ModuleDef(("uuid",))

    __INT_TYPE = ClassDef(("int",), module=__BUILTINS_MODULE, )
    __FLOAT_TYPE = ClassDef(("float",), module=__BUILTINS_MODULE, )
    __UNION_TYPE = ClassDef(("Union",), module=__TYPING_MODULE, )

    __SCALAR_PYTHON_TYPES_BY_JSON_TYPE_AND_FORMAT: t.Final[
        t.Mapping[str, t.Mapping[t.Optional[str], t.Optional[TypeDef]]]
    ] = {
        "null": {
            None: ClassDef(("None",), module=__BUILTINS_MODULE, ),
        },
        "boolean": {
            None: ClassDef(("bool",), module=__BUILTINS_MODULE, ),
        },
        "integer": {
            None: __INT_TYPE,
        },
        "number": {
            None: ClassDef(
                path=(),
                type_parameters=(
                    __INT_TYPE,
                    __FLOAT_TYPE,
                ),
                bases=(__UNION_TYPE,),
            ),
            "int": __INT_TYPE,
            "integer": __INT_TYPE,
            "float": __FLOAT_TYPE,
            "double": __FLOAT_TYPE,
        },
        "string": {
            None: ClassDef(("str",), module=__BUILTINS_MODULE, ),
            "byte": ClassDef(("bytes",), module=__BUILTINS_MODULE, ),
            "date": ClassDef(("date",), module=__DATETIME_MODULE, ),
            "time": ClassDef(("time",), module=__DATETIME_MODULE, ),
            "date-time": ClassDef(("datetime",), module=__DATETIME_MODULE, ),
            "uuid": ClassDef(("UUID",), module=__UUID_MODULE, ),
            "uri": ClassDef(("str",), module=__BUILTINS_MODULE, ),
        },
    }

    def get_type_def_from_json_schema(self, schema: SchemaObject) -> t.Optional[TypeDef]:
        type_, format_ = schema.type_, schema.format_

        if type_ is None:
            return None

        elif isinstance(type_, str):
            return self.__get_type_def_from_json_schema_type(type_, format_)

        else:
            return ClassDef(
                path=("union",),
                type_parameters=make_sequence_of_not_none(*(
                    self.__get_type_def_from_json_schema_type(sub_type, format_)
                    for sub_type in type_
                )),
                bases=(self.__UNION_TYPE,),
            )

    def __get_type_def_from_json_schema_type(
            self,
            type_: t.Optional[str],
            format_: t.Optional[str],
    ) -> t.Optional[TypeDef]:
        if type_ is None:
            return None

        scalar_defs_by_format = self.__SCALAR_PYTHON_TYPES_BY_JSON_TYPE_AND_FORMAT.get(type_) or {}
        if formatted_scalar_type_def := scalar_defs_by_format.get(format_):
            return formatted_scalar_type_def

        return scalar_defs_by_format.get(None)


class SchemaObjectBasedPythonModelDefGenerator(SchemaObjectBasedTypeDefGenerator):
    __BUILTINS_MODULE: t.Final[ModuleDef] = ModuleDef(("builtins",))
    __TYPING_MODULE: t.Final[ModuleDef] = ModuleDef(("typing",))
    __PYDANTIC_MODULE: t.Final[ModuleDef] = ModuleDef(("pydantic",))
    __ENUM_MODULE: t.Final[ModuleDef] = ModuleDef(("enum",))

    __DEFAULT_SCALAR_GENERATOR: t.Final[SchemaObjectBasedTypeDefGenerator] = SchemaObjectBasedPythonTypeDefGenerator()
    __DEFAULT_ANY: t.Final[TypeDef] = ClassDef(("Any",), module=__TYPING_MODULE, )
    __DEFAULT_OBJECT: t.Final[TypeDef] = ClassDef(("BaseModel",), module=__PYDANTIC_MODULE, )
    __DEFAULT_FIELD_INFO: t.Final[TypeDef] = ClassDef(("Field",), module=__PYDANTIC_MODULE, )
    __DEFAULT_MAPPING: t.Final[TypeDef] = ClassDef(("Mapping",), module=__TYPING_MODULE, )
    __DEFAULT_MAPPING_KEY: t.Final[TypeDef] = ClassDef(("str",), module=__BUILTINS_MODULE, )
    __DEFAULT_ARRAY: t.Final[TypeDef] = ClassDef(("Sequence",), module=__TYPING_MODULE, )
    __DEFAULT_SET: t.Final[TypeDef] = ClassDef(("Collection",), module=__TYPING_MODULE, )
    __DEFAULT_TUPLE: t.Final[TypeDef] = ClassDef(("Tuple",), module=__TYPING_MODULE, )
    __DEFAULT_OPTIONAL: t.Final[TypeDef] = ClassDef(("Optional",), module=__TYPING_MODULE, )
    __DEFAULT_UNION: t.Final[TypeDef] = ClassDef(("Union",), module=__TYPING_MODULE, )
    __DEFAULT_ENUM: t.Final[TypeDef] = ClassDef(("Enum",), module=__ENUM_MODULE, )
    __DEFAULT_INLINE_ENUM: t.Final[TypeDef] = ClassDef(("Literal",), module=__TYPING_MODULE, )

    def __init__(
            self,
            scalar_generator: t.Optional[SchemaObjectBasedTypeDefGenerator] = None,
            any_class_def: t.Optional[TypeDef] = None,
            object_class_def: t.Optional[TypeDef] = None,
            mapping_class_def: t.Optional[TypeDef] = None,
            array_class_def: t.Optional[TypeDef] = None,
            set_class_def: t.Optional[TypeDef] = None,
            tuple_class_def: t.Optional[TypeDef] = None,
            optional_class_def: t.Optional[TypeDef] = None,
            union_class_def: t.Optional[TypeDef] = None,
            enum_class_def: t.Optional[TypeDef] = None,
            inline_enum_class_def: t.Optional[TypeDef] = None,
    ) -> None:
        self.__scalar_generator = scalar_generator or self.__DEFAULT_SCALAR_GENERATOR
        self.__any_class_def = any_class_def or self.__DEFAULT_ANY
        self.__object_class_def = object_class_def or self.__DEFAULT_OBJECT
        self.__mapping_class_def = mapping_class_def or self.__DEFAULT_MAPPING
        self.__array_class_def = array_class_def or self.__DEFAULT_ARRAY
        self.__set_class_def = set_class_def or self.__DEFAULT_SET
        self.__tuple_class_def = tuple_class_def or self.__DEFAULT_TUPLE
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

        raise ValueError(schema)

    def __get_path(self, parent: t.Sequence[str], schema: SchemaObject) -> t.Sequence[str]:
        return *parent, self.__get_name(schema)

    def __get_type_ref(self, parent: t.Sequence[str], schema: SchemaObject) -> TypeRef:
        return TypeRef(self.__get_path(parent, schema), schema)

    def __get_optional(self, type_def: TypeDef) -> TypeDef:
        return ClassDef((*type_def.path, "optional",), type_parameters=(type_def,), bases=(self.__optional_class_def,))

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
        field_type_def: TypeDef = self.__get_type_ref(root_path, schema)
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

        if schema.type_ == "object":
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

            if pattern_properties := as_mapping(str, SchemaObject, schema.pattern_properties):
                # TODO: t.Mapping[regex($key), $value]
                raise NotImplementedError

            if as_(bool, schema.additional_properties):
                bases.append(ClassDef(
                    path=(*path, "mapping"),
                    bases=(self.__mapping_class_def,),
                    type_parameters=(self.__DEFAULT_MAPPING_KEY, self.__any_class_def,),
                ))

            elif additional_properties := as_(SchemaObject, schema.additional_properties):
                bases.append(ClassDef(
                    path=(*path, "mapping"),
                    bases=(self.__mapping_class_def,),
                    type_parameters=(self.__DEFAULT_MAPPING_KEY, self.__get_type_ref(path, additional_properties)),
                ))

        elif schema.type_ == "array":
            if schema.items is not False:
                if element_schema := as_(SchemaObject, schema.items):
                    element_def: TypeDef = self.__get_type_ref(path, element_schema)

                elif element_schemas := as_sequence(SchemaObject, schema.items):
                    element_def = self.__get_union(path, "items", element_schemas)

                else:
                    element_def = self.__any_class_def

                bases.append(ClassDef(
                    path=(*path, "array"),
                    type_parameters=(element_def,),
                    bases=(self.__array_class_def,) if not schema.unique_items else (self.__set_class_def,),
                ))

            elif schema.items is False and not schema.unique_items:
                if prefix_items := as_sequence(SchemaObject, schema.prefix_items):
                    # if min_items := as_(int, schema.min_items):
                    #     raise NotImplementedError
                    #
                    # if max_items := as_(int, schema.max_items):
                    #     raise NotImplementedError

                    bases.append(ClassDef(
                        path=(*path, "tuple"),
                        type_parameters=tuple(
                            self.__get_type_ref(path, item_schema)
                            for item_schema in prefix_items
                        ),
                        bases=(self.__tuple_class_def,),
                    ))

                else:
                    raise NotImplementedError

            else:
                raise NotImplementedError

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

            # TODO: make a visitor
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

            elif as_(ModuleDef, type_def):
                pass

            else:
                raise RuntimeError
                # raise_not_exhaustive(type(type_def), type_def)

            yield type_def

    def __resolve_references(
            self,
            type_def: TypeDef,
            references: t.Mapping[TypeRef, TypeDef],
    ) -> TypeDef:
        # TODO: make a visitor
        if class_def := as_(ClassDef, type_def):
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

        elif module_def := as_(ModuleDef, type_def):
            return module_def

        else:
            raise RuntimeError
            # raise_not_exhaustive(type(type_def), type_def)
