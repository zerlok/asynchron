import asyncio
import functools as ft
import inspect
import typing as t
from contextlib import asynccontextmanager

from asynchron.core.controller import Runnable

S = t.TypeVar("S")
S_contra = t.TypeVar("S_contra", contravariant=True)
S_co = t.TypeVar("S_co", covariant=True)

R = t.TypeVar("R", bound=Runnable)
R_contra = t.TypeVar("R_contra", contravariant=True, bound=Runnable)
R_co = t.TypeVar("R_co", covariant=True, bound=Runnable)

F = t.TypeVar("F")
# F_contra = t.TypeVar("F_contra", contravariant=True)
# F_co = t.TypeVar("F_co", covariant=True)

F0 = t.TypeVar("F0", bound=t.Callable[[], object])


# class ServerFactoryFunc(t.Protocol[S_co]):
#     def __call__(self) -> S_co: ...
#
#
# class RunnableFactoryFunc(t.Protocol[S_contra, R_co]):
#     def __call__(self, server: S_contra) -> t.AsyncContextManager[R_co]: ...
#
#
# class ConsumerFacadeFactoryFunc(t.Protocol[S_contra, R_contra, F_co]):
#     def __call__(self, server: S_contra, controller: R_contra) -> F_co: ...
#
#
# class ConsumerBindingFunc(t.Protocol[S_contra, R_contra, F_contra]):
#     def __call__(self, server: S_contra, controller: R_contra, facade: F_contra) -> None: ...


class RunnableFactoryFunc(t.Protocol):
    def __call__(self) -> t.AsyncContextManager[Runnable]: ...


class Application:

    def __init__(
            self,
            runnable_factory: RunnableFactoryFunc,
    ) -> None:
        self.__runnable_factory = runnable_factory

        self.__stop_waiter = None  # type: t.Optional[asyncio.Future[bool]]

    async def run(self) -> None:
        if self.__stop_waiter is not None:
            raise RuntimeError()

        stop_waiter = self.__stop_waiter = asyncio.Future()

        async with self.__runnable_factory() as runnable:
            await runnable.start()
            await stop_waiter
            await runnable.stop()

    def stop(self) -> None:
        if self.__stop_waiter is not None:
            self.__stop_waiter.set_result(True)


class ApplicationBuilder:

    def __init__(self) -> None:
        self.__runnable_factory: t.Optional[RunnableFactoryFunc] = None

    @t.overload
    def runnable_factory(self, func: t.Callable[[], Runnable]) -> t.Callable[[], Runnable]:
        ...

    @t.overload
    def runnable_factory(self, func: t.Callable[[], t.Awaitable[Runnable]]) -> t.Callable[[], t.Awaitable[Runnable]]:
        ...

    @t.overload
    def runnable_factory(
            self,
            func: t.Callable[[], t.AsyncIterator[Runnable]],
    ) -> t.Callable[[], t.AsyncIterator[Runnable]]:
        ...

    def runnable_factory(
            self,
            func: t.Union[
                t.Callable[[], Runnable],
                t.Callable[[], t.Awaitable[Runnable]],
                t.Callable[[], t.AsyncIterator[Runnable]],
            ],
    ) -> t.Union[
        t.Callable[[], Runnable],
        t.Callable[[], t.Awaitable[Runnable]],
        t.Callable[[], t.AsyncIterator[Runnable]],
    ]:
        if inspect.isasyncgenfunction(func):
            asyncgen_func = asynccontextmanager(
                t.cast(t.Callable[..., t.AsyncIterator[object]], func))  # type: ignore[misc]

            @asynccontextmanager  # type: ignore[misc]
            @ft.wraps(asyncgen_func)  # type: ignore[misc]
            async def async_gen_func_wrapper(  # type: ignore[misc]
                    *args: object,
                    **kwargs: object,
            ) -> t.AsyncIterator[Runnable]:
                async with asyncgen_func(*args, **kwargs) as value:
                    if not isinstance(value, Runnable):
                        raise ValueError()

                    yield value

            self.__runnable_factory = t.cast(RunnableFactoryFunc, async_gen_func_wrapper)

        if inspect.iscoroutinefunction(func):
            coroutine_func = t.cast(t.Callable[..., t.Awaitable[object]], func)  # type: ignore[misc]

            @asynccontextmanager  # type: ignore[misc]
            @ft.wraps(coroutine_func)  # type: ignore[misc]
            async def coroutine_func_wrapper(  # type: ignore[misc]
                    *args: object,
                    **kwargs: object,
            ) -> t.AsyncIterator[Runnable]:
                value = await coroutine_func(*args, **kwargs)
                if not isinstance(value, Runnable):
                    raise ValueError()

                yield value

            self.__runnable_factory = t.cast(RunnableFactoryFunc, coroutine_func_wrapper)

        if inspect.isfunction(func):
            sync_func = t.cast(t.Callable[..., object], func)  # type: ignore[misc]

            @asynccontextmanager  # type: ignore[misc]
            @ft.wraps(sync_func)  # type: ignore[misc]
            async def sync_func_wrapper(  # type: ignore[misc]
                    *args: object,
                    **kwargs: object,
            ) -> t.AsyncIterator[Runnable]:
                value = sync_func(*args, **kwargs)
                if not isinstance(value, Runnable):
                    raise ValueError()

                yield value

            self.__runnable_factory = t.cast(RunnableFactoryFunc, sync_func_wrapper)

        else:
            raise ValueError()

        return func

    def build(self) -> Application:
        if self.__runnable_factory is None:
            raise RuntimeError()

        return Application(
            runnable_factory=self.__runnable_factory,
        )
