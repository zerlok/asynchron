import abc
import typing as t

T1 = t.TypeVar("T1")
T2 = t.TypeVar("T2")
T_contra = t.TypeVar("T_contra", contravariant=True)
T_co = t.TypeVar("T_co", covariant=True)


class MessageDecoder(t.Generic[T_contra, T_co], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def decode(self, message: T_contra) -> T_co:
        raise NotImplementedError


class MessageEncoder(t.Generic[T_contra, T_co], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def encode(self, message: T_contra) -> T_co:
        raise NotImplementedError


class MessageSerializer(t.Generic[T1, T2], MessageDecoder[T1, T2], MessageEncoder[T2, T1]):

    @abc.abstractmethod
    def decode(self, message: T1) -> T2:
        raise NotImplementedError

    @abc.abstractmethod
    def encode(self, message: T2) -> T1:
        raise NotImplementedError
