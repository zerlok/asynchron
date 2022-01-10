__all__ = (
    "Walker",
    "DescendantsGetter",
    "DescendantsWalkerFactory",
)

import abc
import typing as t

from asynchron.strict_typing import T, T_co, T_contra


class Walker(t.Generic[T_contra, T_co], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def walk(self, start: T_contra) -> t.Iterable[T_co]:
        raise NotImplementedError


DescendantsGetter = t.Callable[[T], t.Sequence[T]]
DescendantsWalkerFactory = t.Callable[[DescendantsGetter[T_contra]], Walker[T_contra, T_co]]
