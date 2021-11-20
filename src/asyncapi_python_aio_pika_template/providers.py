__all__ = (
    "KeySelector",
)

import typing as t

from dependency_injector.providers import Callable, Provider, deepcopy

T = t.TypeVar("T")


class KeySelector(Provider, t.Generic[T]):
    __slots__ = (
        "__providers_by_key",
        "__inner",
    )

    def __init__(self, providers_by_key: t.Mapping[str, Provider[T]], *args: t.Any, **kwargs: t.Any) -> None:
        self.__providers_by_key = providers_by_key
        self.__inner = Callable(self.__providers_by_key.get, *args, **kwargs)
        super().__init__()

    def __deepcopy__(self, memo: t.Dict[int, t.Any]) -> "KeySelector":
        copied = memo.get(id(self))
        if copied is not None:
            return copied

        copied = self.__class__(
            deepcopy(self.__providers_by_key, memo),
            *deepcopy(self.__inner.args, memo),
            **deepcopy(self.__inner.kwargs, memo),
        )
        self._copy_overridings(copied, memo)

        return copied

    @property
    def related(self) -> t.Iterable[Provider]:
        """Return related providers generator."""
        yield self.__inner
        yield from super().related

    def _provide(self, args: t.Sequence[t.Any], kwargs: t.Mapping[str, t.Any]) -> T:
        key, *args = args
        return self.__inner(key)(*args, **kwargs)

    def keys(self) -> t.Collection[str]:
        return self.__providers_by_key.keys()
