__all__ = (
    "DocumentLoader",
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
from contextlib import contextmanager, suppress
from pathlib import Path
from urllib.parse import urldefrag

from jsonschema import RefResolutionError, RefResolver


class DocumentLoader(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def load(self, uri: str) -> t.Tuple[t.Optional[str], object]:
        raise NotImplementedError


class InMemoryDocumentLoader(DocumentLoader):

    def __init__(self, doc: object) -> None:
        self.__doc = doc

    def reset(self, doc: object) -> None:
        self.__doc = doc

    def load(self, uri: str) -> t.Tuple[t.Optional[str], object]:
        if uri != "":
            return None, None

        return uri, self.__doc


class LocalFileSystemDocumentLoader(DocumentLoader):
    def __init__(self, *parsers: t.Tuple[t.Callable[[t.TextIO], object], t.Type[Exception]]) -> None:
        self.__parsers = parsers

    def load(self, uri: str) -> t.Tuple[t.Optional[str], object]:
        path = Path(uri)
        if not path.exists() or not path.is_file():
            return None, None

        normalized_uri = str(path)

        with path.open("r") as source:
            for func, parse_err in self.__parsers:
                source.seek(0)

                with suppress(parse_err):
                    result = func(source)
                    return normalized_uri, result

            else:
                return None, None


class LocalFileSystemWorkingDirNormalizingDocumentLoader(DocumentLoader):
    def __init__(self, inner: DocumentLoader, root: Path, root_scope: t.Sequence[object] = ()) -> None:
        self.__inner = inner
        self.__stack: t.List[t.Sequence[object]] = [root_scope]
        self.__scopes: t.Dict[t.Sequence[object], Path] = {root_scope: root}

    def load(self, uri: str) -> t.Tuple[t.Optional[str], object]:
        absolute_uri = uri

        if uri.startswith("."):
            cwd = self.__get_current_working_dir()
            absolute_uri = str(cwd.joinpath(uri))

        normalized_uri, result = self.__inner.load(absolute_uri)

        if normalized_uri is not None and absolute_uri != uri:
            self.__reset_current_working_dir(normalized_uri)

        return normalized_uri, result

    @contextmanager
    def use_scope(self, ref: t.Sequence[object]) -> t.Iterable[None]:
        self.__stack.append(ref)

        try:
            yield None

        finally:
            self.__stack.pop(-1)

    def __get_current_working_dir(self) -> Path:
        ref = self.__stack[-1]

        for i in range(len(ref), -1, -1):
            doc_path = self.__scopes.get(ref[:i])
            if doc_path is not None:
                return doc_path.parent

        raise ValueError("No working directory", ref)

    def __reset_current_working_dir(self, uri: str) -> None:
        ref = self.__stack[-1]
        self.__scopes[ref] = Path(uri).absolute()


class SequentialAttemptingDocumentLoader(DocumentLoader):

    def __init__(self, *loaders: DocumentLoader) -> None:
        self.__loaders = loaders

    def load(self, uri: str) -> t.Tuple[t.Optional[str], object]:
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

    def load(self, uri: str) -> t.Tuple[t.Optional[str], object]:
        return self.__load(uri)


class JsonReferenceBasedDocumentPartLoader(DocumentLoader):
    def __init__(self, inner: DocumentLoader) -> None:
        self.__inner = inner

    def load(self, uri: str) -> t.Tuple[t.Optional[str], object]:
        doc_uri, part_fragment = urldefrag(uri)

        normalized_doc_uri, document = self.__inner.load(doc_uri)
        if normalized_doc_uri is None:
            return None, None

        resolver = RefResolver(normalized_doc_uri, document)
        try:
            _, resolved_value = resolver.resolve(f"#{part_fragment}")

        except t.cast(t.Type[Exception], RefResolutionError) as err:
            return None, None

        return "#".join((normalized_doc_uri, part_fragment)), t.cast(object, resolved_value)
