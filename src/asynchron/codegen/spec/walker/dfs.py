__all__ = (
    "DFSPreOrderingWalker",
    "DFSPPostOrderingWalker",
    "DFSWalker",
)

import typing as t

from asynchron.codegen.spec.walker.base import DescendantsGetter, Walker
from asynchron.data_structure import Stack

T = t.TypeVar("T")


class DFSPreOrderingWalker(t.Generic[T], Walker[T, T]):
    @classmethod
    def create(cls, getter: DescendantsGetter[T]) -> "DFSPreOrderingWalker[T]":
        return cls(getter)

    def __init__(
            self,
            descendants_getter: DescendantsGetter[T],
    ) -> None:
        self.__descendants_getter = descendants_getter

    def walk(self, start: T) -> t.Iterator[T]:
        stack = Stack(start)

        for item in stack:
            yield item

            stack.push(*self.__descendants_getter(item))


class DFSPPostOrderingWalker(t.Generic[T], Walker[T, T]):

    @classmethod
    def create(cls, getter: DescendantsGetter[T]) -> "DFSPPostOrderingWalker[T]":
        return cls(getter)

    def __init__(
            self,
            descendants_getter: DescendantsGetter[T],
    ) -> None:
        self.__descendants_getter = descendants_getter

    def walk(self, start: T) -> t.Iterator[T]:
        stack = Stack((start, False))

        for item, is_visited in stack:
            if is_visited:
                yield item

            else:
                stack.push((item, True))

                for sub_item in self.__descendants_getter(item):
                    stack.push((sub_item, False))


DFSWalker = DFSPreOrderingWalker
