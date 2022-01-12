__all__ = (
    "Path",
    "PathWalker",
)

import typing as t
from dataclasses import dataclass

from asynchron.codegen.spec.walker.base import DescendantsGetter, DescendantsWalkerFactory, Walker
from asynchron.codegen.spec.walker.bfs import BFSWalker
from asynchron.codegen.spec.walker.dfs import DFSPPostOrderingWalker, DFSPreOrderingWalker, DFSWalker

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


class PathWalker(t.Generic[T], Walker[T, Path[T]]):
    @classmethod
    def create_bfs(
            cls,
            descendants_getter: DescendantsGetter[T],
    ) -> "PathWalker[T]":
        return cls(BFSWalker.create, descendants_getter)

    @classmethod
    def create_dfs(
            cls,
            descendants_getter: DescendantsGetter[T],
    ) -> "PathWalker[T]":
        return cls(DFSWalker.create, descendants_getter)

    @classmethod
    def create_dfs_pre_ordering(
            cls,
            descendants_getter: DescendantsGetter[T],
    ) -> "PathWalker[T]":
        return cls(DFSPreOrderingWalker.create, descendants_getter)

    @classmethod
    def create_dfs_post_ordering(
            cls,
            descendants_getter: DescendantsGetter[T],
    ) -> "PathWalker[T]":
        return cls(DFSPPostOrderingWalker.create, descendants_getter)

    def __init__(
            self,
            walker_factory: DescendantsWalkerFactory[Path[T], Path[T]],
            descendants_getter: DescendantsGetter[T],
    ) -> None:
        self.__walker = walker_factory(self.__get_descendants)
        self.__descendants_getter = descendants_getter

    def walk(self, start: T) -> t.Iterable[Path[T]]:
        yield from self.__walker.walk(Path((start,)))

    def __get_descendants(self, path: Path[T]) -> t.Sequence[Path[T]]:
        return [
            Path((*path.parts, value))
            for value in self.__descendants_getter(path.value)
        ]
