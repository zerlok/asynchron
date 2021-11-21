__all__ = (
    "BFSSpecObjectWalker",
)

import typing as t

from asyncapi_python_aio_pika_template.spec import SpecObject, SpecObjectVisitor

T = t.TypeVar("T")


class BFSSpecObjectWalker(t.Iterable[T]):

    def __init__(
            self,
            root: T,
            descendants_visitor: SpecObjectVisitor[t.Sequence[T]],
            spec_object_getter: t.Callable[[T], SpecObject],
    ) -> None:
        self.__root = root
        self.__descendants_visitor = descendants_visitor
        self.__spec_object_getter = spec_object_getter

    def __iter__(self) -> t.Iterator[T]:
        yield self.__root

        queue: t.List[SpecObject] = [self.__spec_object_getter(self.__root)]

        while queue:
            obj = queue.pop(0)

            for descendant in obj.accept_visitor(self.__descendants_visitor):
                yield descendant
                queue.append(self.__spec_object_getter(descendant))
