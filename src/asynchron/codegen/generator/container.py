__all__ = (
    "CodeGeneratorContainer",
)

import typing as t
from datetime import datetime
from getpass import getuser

from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Callable, Factory, Object, Provider, Singleton

from asynchron.codegen.app import AsyncApiCodeGenerator
from asynchron.codegen.generator.jinja.jinja_renderer import JinjaTemplateRenderer
from asynchron.codegen.generator.jinja.python_aio_pika import JinjaBasedPythonAioPikaCodeGenerator
from asynchron.codegen.generator.json_schema_python_def import (
    JsonSchemaBasedPythonPrimitiveDefGenerator,
    JsonSchemaBasedPythonStructuredDataModelDefGenerator,
    JsonSchemaBasedTypeDefGenerator,
)
from asynchron.codegen.info import AsyncApiCodeGeneratorMetaInfo


class CodeGeneratorContainer(DeclarativeContainer):
    now: Provider[datetime] = Callable(datetime.utcnow)

    meta_info: Factory[AsyncApiCodeGeneratorMetaInfo] = Factory(
        AsyncApiCodeGeneratorMetaInfo,
        generator_name=Object("asynchron"),
        generator_link=Object("https://github.com/zerlok/asynchron"),
        generator_started_at=now,
        author=Callable(getuser),
    )

    python_primitive_def_generator: Provider[JsonSchemaBasedTypeDefGenerator] = Singleton(
        JsonSchemaBasedPythonPrimitiveDefGenerator,
    )
    python_complex_def_generator: Provider[JsonSchemaBasedTypeDefGenerator] = Singleton(
        JsonSchemaBasedPythonStructuredDataModelDefGenerator,
        python_primitive_def_generator,
    )

    jinja_template_renderer: Provider[t.Optional[JinjaTemplateRenderer]] = Object(
        None,
    )
    jinja_based_python_aio_pika: Provider[AsyncApiCodeGenerator] = Factory(
        JinjaBasedPythonAioPikaCodeGenerator,
        message_def_generator=python_complex_def_generator,
        renderer=jinja_template_renderer,
    )
