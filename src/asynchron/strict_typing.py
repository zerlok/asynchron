__all__ = (
    "T",
    "K",
    "V",
    "T_contra",
    "T_co",
    "F",
    "TF",
    "FW",
    "as_",
    "as_or_default",
    "as_by_key_or_default",
    "as_sequence",
    "as_mapping",
    "as_async_context_manager",
    "get_or_default",
    "get_by_key_or_default",
    "raise_not_exhaustive",
    "make_sequence_of_not_none",
    "gather",
    "gather_with_errors",
    "SerializableObject",
)

import asyncio
import functools as ft
import inspect
import typing as t
from contextlib import asynccontextmanager

T = t.TypeVar("T")
K = t.TypeVar("K", bound=t.Hashable)
V = t.TypeVar("V")
D = t.TypeVar("D")

T_contra = t.TypeVar("T_contra", contravariant=True)
T_co = t.TypeVar("T_co", covariant=True)

F = t.Callable[..., T_co]  # type: ignore[misc]
TF = t.TypeVar("TF", bound=F[t.Any])  # type: ignore[misc]

FW = t.Callable[[TF], TF]


def as_(type_: t.Type[T], obj: object) -> t.Optional[T]:
    return t.cast(T, obj) if isinstance(obj, type_) else None


def as_or_default(type_: t.Type[T], obj: object, default: D) -> t.Union[T, D]:
    value = as_(type_, obj)
    return value if value is not None else default


def as_by_key_or_default(type_: t.Type[T], objs: t.Optional[t.Mapping[K, object]], key: K, default: D) -> t.Union[T, D]:
    value = get_by_key_or_default(objs, key, default)
    return as_or_default(type_, value, default) if value is not default else default


def as_sequence(item: t.Type[T], obj: object) -> t.Optional[t.Sequence[T]]:
    if not isinstance(obj, t.Sequence) or any(not isinstance(o, item) for o in obj):
        return None

    return t.cast(t.Sequence[T], obj)


def as_mapping(key: t.Type[K], value: t.Type[V], obj: object) -> t.Optional[t.Mapping[K, V]]:
    if not isinstance(obj, t.Mapping) \
            or any(not isinstance(k, key) or not isinstance(v, value) for k, v in obj.items()):
        return None

    return t.cast(t.Mapping[K, V], obj)


def as_async_context_manager(type_: t.Type[T], func: object) -> t.Optional[t.AsyncContextManager[T]]:
    if inspect.isasyncgenfunction(func):
        asyncgen_func = asynccontextmanager(
            t.cast(t.Callable[..., t.AsyncIterator[object]], func))  # type: ignore[misc]

        @asynccontextmanager  # type: ignore[misc]
        @ft.wraps(asyncgen_func)  # type: ignore[misc]
        async def async_gen_func_wrapper(*args: object, **kwargs: object) -> t.AsyncIterator[T]:  # type: ignore[misc]
            async with asyncgen_func(*args, **kwargs) as value:
                if not isinstance(value, type_):
                    raise ValueError()

                yield value

        return t.cast(t.AsyncContextManager[T], async_gen_func_wrapper)

    if inspect.iscoroutinefunction(func):
        coroutine_func = t.cast(t.Callable[..., t.Awaitable[object]], func)  # type: ignore[misc]

        @asynccontextmanager  # type: ignore[misc]
        @ft.wraps(coroutine_func)  # type: ignore[misc]
        async def coroutine_func_wrapper(*args: object, **kwargs: object) -> t.AsyncIterator[T]:  # type: ignore[misc]
            value = await coroutine_func(*args, **kwargs)
            if not isinstance(value, type_):
                raise ValueError()

            yield value

        return t.cast(t.AsyncContextManager[T], coroutine_func_wrapper)

    if inspect.isfunction(func):
        sync_func = t.cast(t.Callable[..., object], func)  # type: ignore[misc]

        @asynccontextmanager  # type: ignore[misc]
        @ft.wraps(sync_func)  # type: ignore[misc]
        async def sync_func_wrapper(*args: object, **kwargs: object) -> t.AsyncIterator[T]:  # type: ignore[misc]
            value = sync_func(*args, **kwargs)
            if not isinstance(value, type_):
                raise ValueError()

            yield value

        return t.cast(t.AsyncContextManager[T], sync_func_wrapper)

    return None


def raise_not_exhaustive(*args: t.NoReturn) -> t.NoReturn:
    """A helper to make an exhaustiveness check on python expression. See: https://github.com/python/mypy/issues/5818"""
    raise RuntimeError("Not exhaustive expression", *args)


def get_or_default(value: t.Optional[T], default: D) -> t.Union[T, D]:
    return value if value is not None else default


def get_by_key_or_default(values: t.Optional[t.Mapping[K, V]], key: K, default: D) -> t.Union[V, D]:
    return values.get(key, default) if values is not None else default


def make_sequence_of_not_none(*values: t.Optional[T]) -> t.Sequence[T]:
    return tuple(
        value
        for value in values
        if value is not None
    )


async def gather(coros: t.Iterable[t.Awaitable[T]]) -> t.Sequence[T]:
    return await asyncio.gather(*coros)  # type: ignore


async def gather_with_errors(coros: t.Iterable[t.Awaitable[T]]) -> t.Sequence[t.Union[T, BaseException]]:
    return await asyncio.gather(*coros, return_exceptions=True)  # type: ignore


class SerializableObject(t.Protocol):
    def __getitem__(self, item: t.Union[int, str]) -> "SerializableObject": ...

    def __setitem__(self, item: t.Union[int, str], value: "SerializableObject") -> "SerializableObject": ...
