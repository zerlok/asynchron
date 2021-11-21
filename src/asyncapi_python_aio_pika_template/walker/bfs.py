__all__ = (
    "BFSDescendantSpecObjectWalker",
)

import typing as t

from asyncapi_python_aio_pika_template.spec import SpecObject
from asyncapi_python_aio_pika_template.visitor.descendants import DescendantSpecObject, DescendantsSpecObjectVisitor


class BFSDescendantSpecObjectWalker(t.Iterable[DescendantSpecObject]):

    def __init__(
            self,
            root: SpecObject,
    ) -> None:
        self.__root = DescendantSpecObject(0, root, None)
        self.__descendants_visitor = DescendantsSpecObjectVisitor()

    def __iter__(self) -> t.Iterator[DescendantSpecObject]:
        yield self.__root

        queue: t.List[DescendantSpecObject] = [self.__root]

        while queue:
            obj = queue.pop(0)

            for descendant in obj.value.accept_visitor(self.__descendants_visitor):
                yield descendant

                queue.append(descendant)
