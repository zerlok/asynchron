import asyncio
import os
import typing as t

from asynchron.core.controller import Runnable
from asynchron.strict_typing import FuncWrapper

S = t.TypeVar("S")
S_contra = t.TypeVar("S_contra", contravariant=True)
S_co = t.TypeVar("S_co", covariant=True)

R = t.TypeVar("R", bound=Runnable)
R_contra = t.TypeVar("R_contra", contravariant=True, bound=Runnable)
R_co = t.TypeVar("R_co", covariant=True, bound=Runnable)

F = t.TypeVar("F")
F_contra = t.TypeVar("F_contra", contravariant=True)
F_co = t.TypeVar("F_co", covariant=True)


class ServerFactoryFunc(t.Protocol[S_co]):
    def __call__(self) -> S_co: ...


class RunnableFactoryFunc(t.Protocol[S_contra, R_co]):
    def __call__(self, server: S_contra) -> t.AsyncContextManager[R_co]: ...


class ConsumerFacadeFactoryFunc(t.Protocol[S_contra, R_contra, F_co]):
    def __call__(self, server: S_contra, controller: R_contra) -> F_co: ...


class ConsumerBindingFunc(t.Protocol[S_contra, R_contra, F_contra]):
    def __call__(self, server: S_contra, controller: R_contra, facade: F_contra) -> None: ...


class Application(t.Generic[S, R, F]):

    def __init__(
            self,
            server_factory: ServerFactoryFunc[S],
            runnable_factory: RunnableFactoryFunc[S, R],
            consumer_facade_factory: ConsumerFacadeFactoryFunc[S, R, F],
            consumer_binding: ConsumerBindingFunc[S, R, F],
    ) -> None:
        self.__server_factory = server_factory
        self.__runnable_factory = runnable_factory
        self.__consumer_facade_factory = consumer_facade_factory
        self.__consumer_binding = consumer_binding

        self.__stop_waiter = None  # type: t.Optional[asyncio.Future[bool]]

    async def run(self) -> None:
        if self.__stop_waiter is not None:
            raise RuntimeError()

        stop_waiter = self.__stop_waiter = asyncio.Future()

        server = self.__server_factory()

        async with self.__runnable_factory(server) as runnable:
            facade = self.__consumer_facade_factory(server, runnable)
            self.__consumer_binding(server, runnable, facade)

            await runnable.start()
            await stop_waiter
            await runnable.stop()

    def stop(self) -> None:
        if self.__stop_waiter is not None:
            self.__stop_waiter.set_result(True)


class ApplicationBuilder(t.Generic[S, R, F]):

    def __init__(
            self,
            consumer_binding: ConsumerBindingFunc[S, R, F],
    ) -> None:
        self.__consumer_binding = consumer_binding

        self.__server_factory: t.Optional[ServerFactoryFunc[S]] = None
        self.__runnable_factory: t.Optional[RunnableFactoryFunc[S, R]] = None
        self.__consumer_facade_factory: t.Optional[ConsumerFacadeFactoryFunc[S, R, F]] = None

    def server_factory(self, func: ServerFactoryFunc[S]) -> ServerFactoryFunc[S]:
        self.__server_factory = func

        return func

    def env_name_based_server_factory(self, env: str) -> FuncWrapper[t.Callable[[t.Optional[str]], S]]:
        def inner(func: t.Callable[[t.Optional[str]], S]) -> t.Callable[[t.Optional[str]], S]:
            @self.server_factory
            def wrapper() -> S:
                return func(os.getenv(env))

            return func

        return inner

    def runnable_factory(self, func: RunnableFactoryFunc[S, R]) -> RunnableFactoryFunc[S, R]:
        self.__runnable_factory = func

        return func

    def consumer_facade_factory(self, func: ConsumerFacadeFactoryFunc[S, R, F]) -> ConsumerFacadeFactoryFunc[S, R, F]:
        self.__consumer_facade_factory = func

        return func

    def build(self) -> Application[S, R, F]:
        if self.__server_factory is None:
            raise RuntimeError()

        if self.__runnable_factory is None:
            raise RuntimeError()

        if self.__consumer_facade_factory is None:
            raise RuntimeError()

        return Application(
            server_factory=self.__server_factory,
            runnable_factory=self.__runnable_factory,
            consumer_facade_factory=self.__consumer_facade_factory,
            consumer_binding=self.__consumer_binding,
        )
