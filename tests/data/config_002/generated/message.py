# @formatter:off
import datetime
import pydantic
import typing
import uuid




class MainFooComponentsSchemasFooPropertiesNestedAnyOfWithPropertyNameMatchComponentsSchemasFooPropertiesNestedAnyOfWithPropertyNameMatchAnyOf_1(pydantic.BaseModel):
    shared_prop: typing.Optional[str] = pydantic.Field(
        alias="sharedProp",
    )


class MainFooComponentsSchemasFooPropertiesNestedAnyOfWithPropertyNameMatchComponentsSchemasFooPropertiesNestedAnyOfWithPropertyNameMatchAnyOf_0(pydantic.BaseModel):
    shared_prop: typing.Optional[typing.Union[int, float]] = pydantic.Field(
        alias="sharedProp",
    )


class MainFooComponentsSchemasFooPropertiesNestedOneOfComponentsSchemasFooPropertiesNestedOneOfOneOf_1(pydantic.BaseModel):
    second_one_of_prop: typing.Optional[str] = pydantic.Field(
        alias="secondOneOfProp",
    )


class MainFooComponentsSchemasFooPropertiesNestedOneOfComponentsSchemasFooPropertiesNestedOneOfOneOf_0(pydantic.BaseModel):
    first_one_of_prop: typing.Optional[typing.Union[int, float]] = pydantic.Field(
        alias="firstOneOfProp",
    )


class MainFooComponentsSchemasFooPropertiesNestedAnyOfComponentsSchemasFooPropertiesNestedAnyOfAnyOf_1(pydantic.BaseModel):
    second_any_of_prop: typing.Optional[str] = pydantic.Field(
        alias="secondAnyOfProp",
    )


class MainFooComponentsSchemasFooPropertiesNestedAnyOfComponentsSchemasFooPropertiesNestedAnyOfAnyOf_0(pydantic.BaseModel):
    first_any_of_prop: typing.Optional[typing.Union[int, float]] = pydantic.Field(
        alias="firstAnyOfProp",
    )


class MainFooComponentsSchemasFooPropertiesNestedAllOfComponentsSchemasFooPropertiesNestedAllOfAllOf_1(pydantic.BaseModel):
    second_all_of_prop: typing.Optional[str] = pydantic.Field(
        alias="secondAllOfProp",
    )


class MainFooComponentsSchemasFooPropertiesNestedAllOfComponentsSchemasFooPropertiesNestedAllOfAllOf_0(pydantic.BaseModel):
    first_all_of_prop: typing.Optional[typing.Union[int, float]] = pydantic.Field(
        alias="firstAllOfProp",
    )


class MainFooComponentsSchemasFooPropertiesNestedAllOf(MainFooComponentsSchemasFooPropertiesNestedAllOfComponentsSchemasFooPropertiesNestedAllOfAllOf_0, MainFooComponentsSchemasFooPropertiesNestedAllOfComponentsSchemasFooPropertiesNestedAllOfAllOf_1):
    pass


class MainFooComponentsSchemasFooPropertiesRequiredNestedObjectProp(pydantic.BaseModel):
    number_prop: typing.Optional[typing.Union[int, float]] = pydantic.Field(
        alias="numberProp",
    )


class MainFooComponentsSchemasFooPropertiesNestedNestedObjectPropComponentsSchemasFooPropertiesNestedNestedObjectPropPropertiesNestedObjectProp(pydantic.BaseModel):
    number_object_prop: typing.Optional[typing.Union[int, float]] = pydantic.Field(
        alias="numberObjectProp",
    )


class MainFooComponentsSchemasFooPropertiesNestedNestedObjectProp(pydantic.BaseModel):
    nested_object_prop: typing.Optional[MainFooComponentsSchemasFooPropertiesNestedNestedObjectPropComponentsSchemasFooPropertiesNestedNestedObjectPropPropertiesNestedObjectProp] = pydantic.Field(
        alias="nestedObjectProp",
    )


class MainFooComponentsSchemasFooPropertiesNestedObjectProp(pydantic.BaseModel):
    str_object_prop: typing.Optional[str] = pydantic.Field(
        alias="strObjectProp",
    )


class MainFooComponentsSchemasFooPropertiesStr2nestedObjectMappingPropComponentsSchemasFooPropertiesStr2nestedObjectMappingPropAdditionalProperties(pydantic.BaseModel):
    one: typing.Optional[typing.Union[int, float]] = pydantic.Field(
        alias="one",
    )
    two: typing.Optional[str] = pydantic.Field(
        alias="two",
    )


class MainFoo(pydantic.BaseModel):
    bool_prop: typing.Optional[bool] = pydantic.Field(
        alias="boolProp",
    )
    date_prop: typing.Optional[datetime.date] = pydantic.Field(
        alias="dateProp",
    )
    datetime_prop: typing.Optional[datetime.datetime] = pydantic.Field(
        alias="datetimeProp",
    )
    enum_prop: typing.Optional[typing.Literal['FOO', 'BAR', 'BAZ']] = pydantic.Field(
        alias="enumProp",
    )
    float_number_prop: typing.Optional[float] = pydantic.Field(
        alias="floatNumberProp",
    )
    int_number_prop: typing.Optional[int] = pydantic.Field(
        alias="intNumberProp",
    )
    int_prop: typing.Optional[int] = pydantic.Field(
        alias="intProp",
    )
    nested_all_of: typing.Optional[MainFooComponentsSchemasFooPropertiesNestedAllOf] = pydantic.Field(
        alias="nestedAllOf",
    )
    nested_any_of: typing.Optional[typing.Union[MainFooComponentsSchemasFooPropertiesNestedAnyOfComponentsSchemasFooPropertiesNestedAnyOfAnyOf_0, MainFooComponentsSchemasFooPropertiesNestedAnyOfComponentsSchemasFooPropertiesNestedAnyOfAnyOf_1]] = pydantic.Field(
        alias="nestedAnyOf",
    )
    nested_any_of_with_property_name_match: typing.Optional[typing.Union[MainFooComponentsSchemasFooPropertiesNestedAnyOfWithPropertyNameMatchComponentsSchemasFooPropertiesNestedAnyOfWithPropertyNameMatchAnyOf_0, MainFooComponentsSchemasFooPropertiesNestedAnyOfWithPropertyNameMatchComponentsSchemasFooPropertiesNestedAnyOfWithPropertyNameMatchAnyOf_1]] = pydantic.Field(
        alias="nestedAnyOfWithPropertyNameMatch",
    )
    nested_nested_object_prop: typing.Optional[MainFooComponentsSchemasFooPropertiesNestedNestedObjectProp] = pydantic.Field(
        alias="nestedNestedObjectProp",
    )
    nested_object_prop: typing.Optional[MainFooComponentsSchemasFooPropertiesNestedObjectProp] = pydantic.Field(
        alias="nestedObjectProp",
    )
    nested_one_of: typing.Optional[typing.Union[MainFooComponentsSchemasFooPropertiesNestedOneOfComponentsSchemasFooPropertiesNestedOneOfOneOf_0, MainFooComponentsSchemasFooPropertiesNestedOneOfComponentsSchemasFooPropertiesNestedOneOfOneOf_1]] = pydantic.Field(
        alias="nestedOneOf",
    )
    number_or_array_prop: typing.Optional[typing.Union[typing.Union[int, float]]] = pydantic.Field(
        alias="numberOrArrayProp",
    )
    number_or_str_prop: typing.Optional[typing.Union[typing.Union[int, float], str]] = pydantic.Field(
        alias="numberOrStrProp",
    )
    number_prop: typing.Optional[typing.Union[int, float]] = pydantic.Field(
        alias="numberProp",
    )
    number_sequence_prop: typing.Optional[typing.Sequence[typing.Union[int, float]]] = pydantic.Field(
        alias="numberSequenceProp",
    )
    required_nested_object_prop: MainFooComponentsSchemasFooPropertiesRequiredNestedObjectProp = pydantic.Field(
        alias="requiredNestedObjectProp",
    )
    required_number_prop: typing.Union[int, float] = pydantic.Field(
        alias="requiredNumberProp",
    )
    required_str_prop: str = pydantic.Field(
        alias="requiredStrProp",
    )
    str2nested_object_mapping_prop: typing.Optional[typing.Mapping[str, MainFooComponentsSchemasFooPropertiesStr2nestedObjectMappingPropComponentsSchemasFooPropertiesStr2nestedObjectMappingPropAdditionalProperties]] = pydantic.Field(
        alias="str2nestedObjectMappingProp",
    )
    str2str_mapping_prop: typing.Optional[typing.Mapping[str, str]] = pydantic.Field(
        alias="str2strMappingProp",
    )
    str_collection_prop: typing.Optional[typing.Collection[str]] = pydantic.Field(
        alias="strCollectionProp",
    )
    str_prop: typing.Optional[str] = pydantic.Field(
        alias="strProp",
    )
    str_sequence_prop: typing.Optional[typing.Sequence[str]] = pydantic.Field(
        alias="strSequenceProp",
    )
    time_prop: typing.Optional[datetime.time] = pydantic.Field(
        alias="timeProp",
    )
    tuple2_number_str_prop: typing.Optional[typing.Tuple[typing.Union[int, float], str]] = pydantic.Field(
        alias="tuple2NumberStrProp",
        min_items=2,
    )
    tuple3_number_str_number_prop: typing.Optional[typing.Tuple[typing.Union[int, float], str, typing.Union[int, float]]] = pydantic.Field(
        alias="tuple3NumberStrNumberProp",
        min_items=3,
    )
    uuid_prop: typing.Optional[uuid.UUID] = pydantic.Field(
        alias="uuidProp",
    )








# @formatter:on
