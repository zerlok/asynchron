__all__ = (
    "BFSWalker",
)

import typing as t

from asynchron.codegen.spec.walker.base import DescendantsGetter, Walker

T = t.TypeVar("T")


class BFSWalker(t.Generic[T], Walker[T, T]):

    def __init__(
            self,
            descendants_getter: DescendantsGetter[T],
    ) -> None:
        self.__descendants_getter = descendants_getter

    def walk(self, start: T) -> t.Iterator[T]:
        yield start

        queue: t.List[T] = list(self.__descendants_getter(start))

        while queue:
            item = queue.pop(0)
            yield item

            queue.extend(self.__descendants_getter(item))
