__all__ = (
    "BFSWalker",
)

import typing as t

from asynchron.codegen.spec.walker.base import DescendantsGetter, Walker
from asynchron.data_structure import Queue

T = t.TypeVar("T")


class BFSWalker(t.Generic[T], Walker[T, T]):

    @classmethod
    def create(cls, getter: DescendantsGetter[T]) -> "BFSWalker[T]":
        return cls(getter)

    def __init__(
            self,
            descendants_getter: DescendantsGetter[T],
    ) -> None:
        self.__descendants_getter = descendants_getter

    def walk(self, start: T) -> t.Iterator[T]:
        queue = Queue(start)

        for item in queue:
            yield item

            queue.push(*self.__descendants_getter(item))
