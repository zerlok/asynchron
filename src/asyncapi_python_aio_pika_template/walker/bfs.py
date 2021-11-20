__all__ = (
    "BFSSpecObjectWalker",
)

import typing as t

from asyncapi_python_aio_pika_template.spec import SpecObject, SpecObjectVisitor


class BFSSpecObjectWalker(t.Iterable[t.Tuple[str, SpecObject]]):

    def __init__(
            self,
            root: SpecObject,
            descendants_visitor: SpecObjectVisitor[t.Sequence[t.Tuple[str, SpecObject]]],
    ) -> None:
        self.__root = root
        self.__descendants_visitor = descendants_visitor

    def __iter__(self) -> t.Iterator[t.Tuple[str, SpecObject]]:
        yield self.__root

        queue: t.List[SpecObject] = [self.__root]

        while queue:
            obj = queue.pop(0)

            for key, descendant in obj.accept_visitor(self.__descendants_visitor):
                yield key, descendant
                queue.append(descendant)
