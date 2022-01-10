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
    "as_sequence",
    "as_mapping",
    "as_async_context_manager",
    "get_or_default",
    "raise_not_exhaustive",
    "make_sequence_of_not_none",
    "gather",
    "gather_with_errors",
    # "MethodOverload",
    "SerializableObject",
)

import abc
import asyncio
import functools as ft
import inspect
import typing as t
from contextlib import asynccontextmanager

T = t.TypeVar("T")
K = t.TypeVar("K", bound=t.Hashable)
V = t.TypeVar("V")

T_contra = t.TypeVar("T_contra", contravariant=True)
T_co = t.TypeVar("T_co", covariant=True)

F = t.Callable[..., T_co]  # type: ignore[misc]
TF = t.TypeVar("TF", bound=F[t.Any])  # type: ignore[misc]

FW = t.Callable[[TF], TF]


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


def get_or_default(value: t.Optional[T], default: T) -> T:
    return value if value is not None else default


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


# class MethodOverload(t.Generic[T]):
#     def __init__(self, func: F[T]) -> None:
#         self.__dispatcher = ft.singledispatchmethod(func)
#
#     def register(self, cls: t.Type[object]) -> FW[F[T]]:
#         return self.__dispatcher.register(cls)  # type: ignore[misc]
#
#     def __call__(self, *args: object, **kwargs: object) -> T:
#         return self.__dispatcher(*args, **kwargs)


class SerializableObject(t.Protocol):
    def __getitem__(self, item: t.Union[int, str]) -> "SerializableObject": ...

    def __setitem__(self, item: t.Union[int, str], value: "SerializableObject") -> "SerializableObject": ...
