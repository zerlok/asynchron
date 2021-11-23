__all__ = (
    "BFSWalker",
)

import typing as t

T = t.TypeVar("T")


class BFSWalker(t.Iterable[T]):

    def __init__(
            self,
            root: T,
            descendants_getter: t.Callable[[T], t.Sequence[T]],
    ) -> None:
        self.__root = root
        self.__descendants_getter = descendants_getter

    def __iter__(self) -> t.Iterator[T]:
        yield self.__root

        queue: t.List[T] = [*self.__descendants_getter(self.__root)]

        while queue:
            item = queue.pop(0)
            yield item

            queue.extend(self.__descendants_getter(item))
