__all__ = (
    "Stack",
    "Queue",
)

import typing as t

T = t.TypeVar("T")


class Stack(t.Generic[T], t.Sized, t.Iterable[T]):
    __slots__ = ("__data",)

    def __init__(self, *values: T) -> None:
        self.__data: t.List[T] = []
        self.push(*values)

    def __len__(self) -> int:
        return len(self.__data)

    def __iter__(self) -> t.Iterator[T]:
        while self.__data:
            yield self.pop()

    def push(self, *values: T) -> None:
        self.__data.extend(reversed(values))

    def pop(self) -> T:
        return self.__data.pop()


class Queue(t.Generic[T], t.Sized):
    __slots__ = ("__data",)

    def __init__(self, *values: T) -> None:
        self.__data: t.List[T] = []
        self.push(*values)

    def __len__(self) -> int:
        return len(self.__data)

    def __iter__(self) -> t.Iterator[T]:
        while self.__data:
            yield self.pop()

    def push(self, *values: T) -> None:
        self.__data.extend(values)

    def pop(self) -> T:
        return self.__data.pop(0)
