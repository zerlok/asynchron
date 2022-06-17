__all__ = (
    "DocumentLoader",
    "ScopeContextManager",
    "InMemoryDocumentLoader",
    "LocalFileSystemDocumentLoader",
    "LocalFileSystemWorkingDirNormalizingDocumentLoader",
    "SequentialAttemptingDocumentLoader",
    "CachedDocumentLoader",
    "JsonReferenceBasedDocumentPartLoader",
)

import abc
import functools as ft
import typing as t
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urldefrag

from jsonschema import RefResolutionError, RefResolver

from asynchron.codegen.spec.asyncapi import (
    JsonReference,
    LocalFileSystemDocumentJsonReference,
    SameDocumentJsonReference,
)
from asynchron.codegen.spec.walker.spec_object_path import SpecObjectPath


class DocumentLoader(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def load(self, uri: JsonReference) -> t.Tuple[t.Optional[JsonReference], object]:
        raise NotImplementedError


class ScopeContextManager(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def use_scope(self, key: SpecObjectPath) -> t.ContextManager[None]:
        raise NotImplementedError


class InMemoryDocumentLoader(DocumentLoader):

    def __init__(self, doc: object, doc_uri: JsonReference) -> None:
        self.__doc = doc
        self.__doc_uri = doc_uri

    def reset(self, doc: object) -> None:
        self.__doc = doc

    def load(self, uri: JsonReference) -> t.Tuple[t.Optional[JsonReference], object]:
        if uri != self.__doc_uri:
            return None, None

        return uri, self.__doc


class LocalFileSystemDocumentLoader(DocumentLoader):
    def __init__(self, *parsers: t.Tuple[t.Callable[[t.TextIO], object], t.Type[Exception]]) -> None:
        self.__parsers = parsers

    def load(self, uri: JsonReference) -> t.Tuple[t.Optional[JsonReference], object]:
        path = Path(uri)
        if not path.exists() or not path.is_file():
            return None, None

        normalized_uri = LocalFileSystemDocumentJsonReference(str(path))

        with path.open("r") as source:
            for func, parse_err in self.__parsers:
                source.seek(0)

                # noinspection PyBroadException
                try:
                    result = func(source)

                except parse_err:
                    continue

                else:
                    return normalized_uri, result

            else:
                return None, None


class LocalFileSystemWorkingDirNormalizingDocumentLoader(DocumentLoader, ScopeContextManager):
    def __init__(
            self,
            inner: DocumentLoader,
            root: Path,
            root_key: SpecObjectPath = (),
    ) -> None:
        self.__inner = inner
        self.__scope_stack: t.List[SpecObjectPath] = [root_key]
        self.__paths_by_scopes: t.Dict[SpecObjectPath, Path] = {root_key: root}

    def load(self, uri: JsonReference) -> t.Tuple[t.Optional[JsonReference], object]:
        absolute_uri = uri

        if isinstance(uri, SameDocumentJsonReference):
            absolute_uri = LocalFileSystemDocumentJsonReference(self.__get_current_working_path())

        elif isinstance(uri, LocalFileSystemDocumentJsonReference) and uri.startswith("."):
            absolute_uri = LocalFileSystemDocumentJsonReference(
                self.__get_current_working_path().parent.joinpath(uri))

        normalized_uri, result = self.__inner.load(absolute_uri)

        if normalized_uri is not None and absolute_uri != uri:
            self.__reset_current_working_path(normalized_uri)

        return normalized_uri, result

    @contextmanager
    def use_scope(self, key: SpecObjectPath) -> t.Iterator[None]:
        self.__scope_stack.append(key)

        try:
            yield None

        finally:
            self.__scope_stack.pop(-1)

    def __get_current_working_path(self) -> Path:
        scope = self.__scope_stack[-1]

        for i in range(len(scope), -1, -1):
            doc_path = self.__paths_by_scopes.get(scope[:i])
            if doc_path is not None:
                return doc_path

        raise ValueError("No working directory", scope)

    def __reset_current_working_path(self, uri: JsonReference) -> None:
        scope = self.__scope_stack[-1]
        self.__paths_by_scopes[scope] = Path(uri).absolute()


class SequentialAttemptingDocumentLoader(DocumentLoader):

    def __init__(self, *loaders: DocumentLoader) -> None:
        self.__loaders = loaders

    def load(self, uri: JsonReference) -> t.Tuple[t.Optional[JsonReference], object]:
        for loader in self.__loaders:
            normalized_uri, result = loader.load(uri)
            if normalized_uri is not None:
                return normalized_uri, result

        return None, None


class CachedDocumentLoader(DocumentLoader):
    def __init__(
            self,
            inner: DocumentLoader,
            cache_size: t.Optional[int] = 256,
    ) -> None:
        self.__load = ft.lru_cache(cache_size)(inner.load)

    def load(self, uri: JsonReference) -> t.Tuple[t.Optional[JsonReference], object]:
        return self.__load(uri)

    def reset(self) -> None:
        self.__load.cache_clear()


class JsonReferenceBasedDocumentPartLoader(DocumentLoader):
    def __init__(self, inner: DocumentLoader) -> None:
        self.__inner = inner

    def load(self, uri: JsonReference) -> t.Tuple[t.Optional[JsonReference], object]:
        doc_uri, part_fragment = self.__split(uri)

        normalized_doc_uri, document = self.__inner.load(doc_uri)
        if normalized_doc_uri is None:
            return None, None

        resolver = RefResolver(normalized_doc_uri, document)
        try:
            _, resolved_value = resolver.resolve(f"#{part_fragment}")

        except t.cast(t.Type[Exception], RefResolutionError) as err:
            return None, None

        return type(normalized_doc_uri)("#".join((normalized_doc_uri, part_fragment))), t.cast(object, resolved_value)

    def __split(self, uri: JsonReference) -> t.Tuple[JsonReference, SameDocumentJsonReference]:
        doc_uri, part_fragment = urldefrag(uri)

        return type(uri)(doc_uri), SameDocumentJsonReference(part_fragment)
