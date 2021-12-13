__all__ = (
    "MappingValueSelector",
)

import typing as t

from dependency_injector.providers import Callable, Provider, deepcopy

K = t.TypeVar("K")
V = t.TypeVar("V")

_MISSED: t.Final[object] = object()


class MappingValueSelector(t.Generic[K, V], Provider[V]):
    """
    Returns an instance from a provider, that was registered by specified key.

    See suggestion: https://github.com/ets-labs/python-dependency-injector/issues/530
    """

    __slots__ = (
        "__providers_by_key",
        "__inner",
    )

    def __init__(self, providers_by_key: t.Mapping[K, Provider[V]], key: t.Union[K, object] = _MISSED) -> None:
        self.__providers_by_key = providers_by_key
        self.__inner: Callable[V] = (
            Callable(self.__provide_by_key, key)
            if key is not _MISSED
            else Callable(self.__provide_by_key)
        )
        super().__init__()

    def __deepcopy__(self, memo: t.Optional[t.Dict[object, object]]) -> "MappingValueSelector[K, V]":
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
    def related(self) -> t.Iterator[Provider[V]]:
        """Return related providers generator."""
        yield self.__inner
        yield from super().related

    def _provide(self, args: t.Sequence[object], kwargs: t.Mapping[str, object]) -> V:
        return self.__inner(*args, **kwargs)

    def __provide_by_key(self, __key: K, *args: object, **kwargs: object) -> V:
        return self.__providers_by_key[__key](*args, **kwargs)

    @property
    def keys(self) -> t.Collection[K]:
        return self.__providers_by_key.keys()

    @property
    def providers(self) -> t.Mapping[K, Provider[V]]:
        return self.__providers_by_key
