__all__ = (
    "DFSWalker",
)

import typing as t

from asynchron.codegen.spec.walker.base import DescendantsGetter, Walker

T = t.TypeVar("T")


class DFSWalker(t.Generic[T], Walker[T, T]):

    def __init__(
            self,
            descendants_getter: DescendantsGetter[T],
    ) -> None:
        self.__descendants_getter = descendants_getter

    def walk(self, start: T) -> t.Iterator[T]:
        yield start

        stack: t.List[T] = list(self.__descendants_getter(start))

        while stack:
            item = stack.pop()
            yield item

            for sub_item in reversed(self.__descendants_getter(item)):
                stack.insert(0, sub_item)
