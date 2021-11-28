__all__ = (
    "KeySelector",
)

import typing as t

from dependency_injector.providers import Callable, Provider, deepcopy

T = t.TypeVar("T")

_MISSED = object()


class KeySelector(Provider[T]):
    """
    Returns an instance from a provider, that was registered with specified key.

    See suggestion: https://github.com/ets-labs/python-dependency-injector/issues/530
    """

    __slots__ = (
        "__providers_by_key",
        "__inner",
    )

    def __init__(self, providers_by_key: t.Mapping[str, Provider[T]], key: t.Union[str, object] = _MISSED) -> None:
        self.__providers_by_key = providers_by_key
        self.__inner: Callable[T] = (
            Callable(self.__provide_by_key, key)
            if key is not _MISSED
            else Callable(self.__provide_by_key)
        )
        super().__init__()

    def __deepcopy__(self, memo: t.Optional[t.Dict[t.Any, t.Any]]) -> "KeySelector[T]":
        if memo is not None:
            copied = memo.get(id(self))
            if copied is not None and isinstance(copied, self.__class__):
                return copied

        copied = self.__class__(
            deepcopy(self.__providers_by_key, memo),
            *deepcopy(self.__inner.args, memo),
            **deepcopy(self.__inner.kwargs, memo),
        )
        self._copy_overridings(copied, memo)

        return copied

    @property
    def related(self) -> t.Iterator[Provider[T]]:
        """Return related providers generator."""
        yield self.__inner
        yield from super().related

    def _provide(self, args: t.Sequence[t.Any], kwargs: t.Mapping[str, t.Any]) -> T:
        return self.__inner(*args, **kwargs)

    def __provide_by_key(self, __key: str, *args: t.Any, **kwargs: t.Any) -> T:
        return self.__providers_by_key[__key](*args, **kwargs)

    @property
    def keys(self) -> t.Collection[str]:
        return self.__providers_by_key.keys()

    @property
    def providers(self) -> t.Mapping[str, Provider[T]]:
        return self.__providers_by_key
