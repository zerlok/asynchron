__all__ = (
    "JsonReferenceResolvingTransformer",
)

import json
import typing as t
from pathlib import Path

import yaml

from asynchron.codegen.app import AsyncApiConfigTransformer, AsyncApiConfigTransformerError
from asynchron.codegen.spec.asyncapi import (
    AsyncAPIObject,
    JsonReference,
    ReferenceObject,
    SpecObject,
)
from asynchron.codegen.spec.document.loader import (
    CachedDocumentLoader,
    DocumentLoader,
    InMemoryDocumentLoader,
    JsonReferenceBasedDocumentPartLoader,
    LocalFileSystemDocumentLoader,
    LocalFileSystemWorkingDirNormalizingDocumentLoader,
    SequentialAttemptingDocumentLoader,
)
from asynchron.codegen.spec.walker.spec_object_path import SpecObjectPath, SpecObjectWithPathWalker
from asynchron.serializable_object_modifier import SerializableObjectModifier
from asynchron.strict_typing import SerializableObject, as_, make_sequence_of_not_none


class JsonReferenceResolvingTransformer(AsyncApiConfigTransformer):

    def __init__(
            self,
            config_path: Path,
            modifier: t.Optional[SerializableObjectModifier] = None,
            max_iterations: int = 256,
            external_document_loader: t.Optional[DocumentLoader] = None,
    ) -> None:
        if not (0 < max_iterations <= 256):
            raise ValueError("Max iterations not in valid values range", max_iterations)

        self.__config_path = config_path
        self.__modifier = modifier or SerializableObjectModifier()
        self.__max_iterations = max_iterations
        self.__external_document_loader = external_document_loader

        self.__walker = SpecObjectWithPathWalker.create_bfs()

    def transform(self, config: AsyncAPIObject) -> AsyncAPIObject:
        cfg = config

        resolver = _Resolver(self.__config_path, config, self.__external_document_loader)

        # TODO: get total reference graph and resolve it ordering by dependencies or cancel resolution if graph has
        #  cycles.
        for _ in self.__iter_max_iterations():
            changes = [
                (obj_path, resolver.resolve(obj_path, json_ref))
                for obj_path, json_ref in self.__iter_references(cfg)
            ]
            if not changes:
                break

            cfg = self.__modifier.replace(
                target=cfg,
                changes=changes,
            )
            resolver.reset(cfg)

        return cfg

    def __iter_max_iterations(self) -> t.Iterable[int]:
        for i in range(self.__max_iterations):
            yield i

        else:
            raise RuntimeError("Iteration limits on reference resolving is exceeded", self.__max_iterations)

    def __iter_references(self, config: SpecObject) -> t.Iterable[t.Tuple[SpecObjectPath, JsonReference]]:
        for path, value in self.__walker.walk(config):
            # FIXME: mypy can't infer the type of `value`
            #  error: Expression type contains "Any" (has type "Type[ReferenceObject]")  [misc]
            if ref_obj := as_(ReferenceObject, value):  # type: ignore[misc]
                yield path, ref_obj.ref


class _Resolver:
    def __init__(
            self,
            path: Path,
            config: AsyncAPIObject,
            extra_loader: DocumentLoader,
            document_cache_size: int = 32,
            document_part_cache_size: int = 1024,
    ) -> None:
        self.__config = config

        self.__in_mem_loader = InMemoryDocumentLoader(self.__serialize(config))
        self.__working_dir_loader = LocalFileSystemWorkingDirNormalizingDocumentLoader(
            LocalFileSystemDocumentLoader(
                (yaml.safe_load, Exception),
                (json.load, json.JSONDecodeError),
            ),
            root=path,
            root_key=(),
        )
        self.__reference_loader = CachedDocumentLoader(
            JsonReferenceBasedDocumentPartLoader(
                CachedDocumentLoader(
                    SequentialAttemptingDocumentLoader(*make_sequence_of_not_none(
                        self.__in_mem_loader,
                        self.__working_dir_loader,
                        extra_loader,
                    )),
                    cache_size=document_cache_size,
                ),
            ),
            cache_size=document_part_cache_size,
        )

    def resolve(self, key: SpecObjectPath, ref: JsonReference) -> SerializableObject:
        with self.__working_dir_loader.use_scope(key):
            uri, value = self.__reference_loader.load(ref)

        if uri is None:
            raise AsyncApiConfigTransformerError("Invalid json reference", key, ref)

        return t.cast(SerializableObject, value)

    def reset(self, config: AsyncAPIObject) -> None:
        if config is not self.__config:
            self.__in_mem_loader.reset(self.__serialize(config))

    def __serialize(self, config: AsyncAPIObject) -> SerializableObject:
        return t.cast(SerializableObject, config.dict(by_alias=True, exclude_none=True))
