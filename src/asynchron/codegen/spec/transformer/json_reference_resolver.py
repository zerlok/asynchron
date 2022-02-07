__all__ = (
    "JsonReferenceResolvingTransformer",
)

import json
import typing as t
from pathlib import Path

import yaml

from asynchron.codegen.app import AsyncApiConfigTransformer
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

        def serialize(c: AsyncAPIObject) -> SerializableObject:
            return t.cast(SerializableObject, c.dict(by_alias=True, exclude_none=True))

        in_mem_doc_loader = InMemoryDocumentLoader(serialize(cfg))
        working_dir_loader, reference_loader = self.__create_loader(in_mem_doc_loader)

        def resolve(path: SpecObjectPath, ref: JsonReference) -> SerializableObject:
            with working_dir_loader.use_scope(path):
                uri, value = reference_loader.load(ref)

            return t.cast(SerializableObject, value)

        # TODO: get total reference graph and resolve it ordering by dependencies or cancel resolution if graph has
        #  cycles.
        for _ in self.__iter_max_iterations():
            in_mem_doc_loader.reset(serialize(cfg))

            changes = [
                (obj_path, resolve(obj_path, json_ref))
                for obj_path, json_ref in self.__iter_references(cfg)
            ]
            if not changes:
                break

            cfg = self.__modifier.replace(
                target=cfg,
                changes=changes,
            )

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

    def __create_loader(
            self,
            main: DocumentLoader,
    ) -> t.Tuple["LocalFileSystemWorkingDirNormalizingDocumentLoader", DocumentLoader]:
        working_dir_loader = LocalFileSystemWorkingDirNormalizingDocumentLoader(
            LocalFileSystemDocumentLoader(
                (yaml.safe_load, Exception),
                (json.load, json.JSONDecodeError),
            ),
            root=self.__config_path,
            root_scope=(),
        )

        reference_loader = CachedDocumentLoader(
            JsonReferenceBasedDocumentPartLoader(
                CachedDocumentLoader(
                    SequentialAttemptingDocumentLoader(*make_sequence_of_not_none(
                        main,
                        working_dir_loader,
                        self.__external_document_loader,
                    )),
                    cache_size=32,
                ),
            ),
            cache_size=1024,
        )

        return working_dir_loader, reference_loader
