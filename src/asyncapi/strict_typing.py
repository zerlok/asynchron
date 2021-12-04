__all__ = (
    "as_",
    "as_sequence",
    "as_mapping",
    "raise_not_exhaustive",
    "gather",
    "gather_with_errors",
)

import asyncio
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


def raise_not_exhaustive(*args: t.NoReturn) -> t.NoReturn:
    """A helper to make an exhaustiveness check on python expression. See: https://github.com/python/mypy/issues/5818"""
    raise RuntimeError("Not exhaustive expression", *args)


async def gather(coros: t.Iterable[t.Awaitable[T]]) -> t.Sequence[T]:
    return await asyncio.gather(*coros)  # type: ignore


async def gather_with_errors(coros: t.Iterable[t.Awaitable[T]]) -> t.Sequence[t.Union[T, BaseException]]:
    return await asyncio.gather(*coros, return_exceptions=True)  # type: ignore
