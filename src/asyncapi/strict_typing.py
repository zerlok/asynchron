__all__ = (
    "as_",
    "as_sequence",
    "as_mapping",
)

import typing as t

T = t.TypeVar("T")
K = t.TypeVar("K")
V = t.TypeVar("V")


def as_(type_: t.Type[T], obj: object) -> t.Optional[T]:
    if not isinstance(obj, type_):
        return None

    return t.cast(T, obj)


def as_sequence(item: t.Type[T], obj: object) -> t.Optional[t.Sequence[T]]:
    if not isinstance(obj, t.Sequence) or any(not isinstance(o, item) for o in obj):
        return None

    return t.cast(t.Sequence[T], obj)


def as_mapping(key: t.Type[K], value: t.Type[V], obj: object) -> t.Optional[t.Mapping[K, V]]:
    if not isinstance(obj, t.Mapping) \
            or any(not isinstance(k, key) or not isinstance(v, value) for k, v in obj.items()):
        return None

    return t.cast(t.Mapping[K, V], obj)
