__all__ = (
    "Path",
    "BFSPathWalker",
)

import typing as t
from dataclasses import dataclass

from asynchron.spec.walker.bfs import BFSWalker

T = t.TypeVar("T")


@dataclass(frozen=True)
class Path(t.Generic[T]):
    parts: t.Sequence[T]

    @property
    def value(self) -> T:
        return self.parts[-1]

    @property
    def parent(self) -> t.Optional[T]:
        return self.parts[-2] if len(self.parts) > 1 else None


class BFSPathWalker(t.Iterable[Path[T]]):
    def __init__(
            self,
            root: T,
            descendants_getter: t.Callable[[T], t.Sequence[T]],
    ) -> None:
        self.__root = Path((root,))
        self.__descendants_getter = descendants_getter
        self.__inner = BFSWalker(self.__root, self.__get_descendants)

    def __get_descendants(self, path: Path[T]) -> t.Sequence[Path[T]]:
        return [
            Path((*path.parts, value))
            for value in self.__descendants_getter(path.value)
        ]

    def __iter__(self) -> t.Iterator[Path[T]]:
        return iter(self.__inner)
