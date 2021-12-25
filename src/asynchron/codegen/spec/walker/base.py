__all__ = (
    "Walker",
    "DescendantsGetter",
    "DescendantsWalkerFactory",
)

import abc
import typing as t

T = t.TypeVar("T")
T_contra = t.TypeVar("T_contra", contravariant=True)
T_co = t.TypeVar("T_co", covariant=True)


class Walker(t.Generic[T_contra, T_co], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def walk(self, start: T_contra) -> t.Iterable[T_co]:
        raise NotImplementedError


class DescendantsGetter(t.Protocol[T]):
    def __call__(self, item: T) -> t.Sequence[T]: ...


class DescendantsWalkerFactory(t.Generic[T_contra, T_co]):
    def __call__(self, descendants_getter: DescendantsGetter[T_contra]) -> Walker[T_contra, T_co]: ...
