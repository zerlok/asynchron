import itertools as it
import typing as t

from asynchron.codegen.spec.base import SpecObject, SpecObjectVisitor
from asynchron.codegen.spec.visitor.referenced_descendants import (
    ReferencedDescendantSpecObjectVisitor,
    ReferencedSpecObject,
)
from asynchron.codegen.spec.walker.base import DescendantsWalkerFactory, Walker
from asynchron.codegen.spec.walker.path import Path, PathWalker

SpecObjectPath = t.Sequence[t.Union[int, str]]


class SpecObjectWithPathWalker(Walker[SpecObject, t.Tuple[SpecObjectPath, SpecObject]]):
    __DEFAULT_VISITOR: t.Final[SpecObjectVisitor[t.Sequence[ReferencedSpecObject]]] \
        = ReferencedDescendantSpecObjectVisitor()

    @classmethod
    def create_bfs(
            cls,
            visitor: t.Optional[SpecObjectVisitor[t.Sequence[ReferencedSpecObject]]] = None,
    ) -> "SpecObjectWithPathWalker":
        return cls(
            walker_factory=PathWalker.create_bfs,
            visitor=visitor,
        )

    @classmethod
    def create_dfs(
            cls,
            visitor: t.Optional[SpecObjectVisitor[t.Sequence[ReferencedSpecObject]]] = None,
    ) -> "SpecObjectWithPathWalker":
        return cls(
            walker_factory=PathWalker.create_dfs,
            visitor=visitor,
        )

    @classmethod
    def create_dfs_pre_ordering(
            cls,
            visitor: t.Optional[SpecObjectVisitor[t.Sequence[ReferencedSpecObject]]] = None,
    ) -> "SpecObjectWithPathWalker":
        return cls(
            walker_factory=PathWalker.create_dfs_pre_ordering,
            visitor=visitor,
        )

    @classmethod
    def create_dfs_post_ordering(
            cls,
            visitor: t.Optional[SpecObjectVisitor[t.Sequence[ReferencedSpecObject]]] = None,
    ) -> "SpecObjectWithPathWalker":
        return cls(
            walker_factory=PathWalker.create_dfs_post_ordering,
            visitor=visitor,
        )
    
    def __init__(
            self,
            walker_factory: DescendantsWalkerFactory[ReferencedSpecObject, Path[ReferencedSpecObject]],
            visitor: t.Optional[SpecObjectVisitor[t.Sequence[ReferencedSpecObject]]] = None,
    ) -> None:
        self.__walker = walker_factory(self.__get_spec_object_descendants)
        self.__visitor = visitor or self.__DEFAULT_VISITOR

    def walk(self, start: SpecObject) -> t.Iterable[t.Tuple[SpecObjectPath, SpecObject]]:
        for path in self.__walker.walk(ReferencedSpecObject((), start)):
            ref = tuple(it.chain.from_iterable(part.ref for part in path.parts))
            value = path.value.value

            yield ref, value

    def __get_spec_object_descendants(self, obj: ReferencedSpecObject) -> t.Sequence[ReferencedSpecObject]:
        return obj.value.accept_visitor(self.__visitor)
