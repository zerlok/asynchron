__all__ = (
    "SerializableObjectModifier",
)

import functools as ft
import typing as t
from dataclasses import dataclass, is_dataclass

from pydantic import BaseModel

from asynchron.strict_typing import SerializableObject

T = t.TypeVar("T")


class SerializableObjectModifier:
    def __init__(
            self,
            serializer: t.Optional[t.Callable[[object], SerializableObject]] = None,
            deserializer: t.Optional[t.Callable[[T, SerializableObject], T]] = None,
    ) -> None:
        self.__serializer = serializer or self.__serialize_object
        self.__deserializer = deserializer or self.__deserialize_object

    def replace(
            self,
            target: T,
            changes: t.Sequence[t.Tuple[t.Sequence[t.Union[int, str]], object]],
    ) -> T:
        if not changes:
            return target

        changed_serialized_root = self.__serializer(target)

        for path, changed_value in changes:
            serialized_changed_value = self.__serializer(changed_value)

            changed_serialized_target = changed_serialized_root
            *parts, last = path
            for part in parts:
                changed_serialized_target = changed_serialized_target[part]

            changed_serialized_target[last] = serialized_changed_value

        changed_target = self.__deserializer(target, changed_serialized_root)

        return changed_target

    @ft.singledispatchmethod
    def __serialize_object(self, obj: object) -> SerializableObject:
        raise TypeError("Unsupported value type", type(obj), obj)

    @__serialize_object.register(type(None))
    @__serialize_object.register(bool)
    @__serialize_object.register(int)
    @__serialize_object.register(float)
    @__serialize_object.register(str)
    @__serialize_object.register(list)
    @__serialize_object.register(dict)
    def __serialize_json_serializable_object(
            self,
            obj: object,
    ) -> SerializableObject:
        return t.cast(SerializableObject, obj)

    @__serialize_object.register(BaseModel)
    def __serialize_pydantic_model(self, obj: BaseModel) -> SerializableObject:
        return t.cast(SerializableObject, obj.dict(by_alias=True, exclude_none=True))

    @ft.singledispatchmethod
    def __deserialize_object(self, source: T, obj: SerializableObject) -> T:
        raise TypeError("Unsupported value type", type(source), obj)

    @__deserialize_object.register(type(None))
    @__deserialize_object.register(bool)
    @__deserialize_object.register(int)
    @__deserialize_object.register(float)
    @__deserialize_object.register(str)
    @__deserialize_object.register(list)
    @__deserialize_object.register(dict)
    def __deserialize_json_serializable_object(
            self,
            source: T,
            obj: SerializableObject,
    ) -> T:
        return t.cast(T, obj)

    @__deserialize_object.register(BaseModel)
    def __deserialize_pydantic_model(self, source: BaseModel, obj: SerializableObject) -> BaseModel:
        return source.__class__.parse_obj(obj)