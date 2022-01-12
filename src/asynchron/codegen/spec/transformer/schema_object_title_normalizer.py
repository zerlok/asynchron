__all__ = (
    "SpecObjectTransformer",
    "SpecObjectTitleNormalizer",
)

import re
import typing as t

import stringcase

from asynchron.codegen.app import AsyncApiConfigTransformer
from asynchron.codegen.spec.base import (
    AsyncAPIObject,
    ChannelBindingsObject,
    ChannelItemObject,
    ChannelsObject,
    ComponentsObject,
    ContactObject, CorrelationIdObject,
    DefaultContentType, ExternalDocumentationObject, Identifier, InfoObject, LicenseObject, MessageBindingsObject,
    MessageExampleObject,
    MessageObject,
    MessageTraitObject,
    OAuthFlowObject,
    OAuthFlowsObject,
    OperationBindingsObject,
    OperationObject,
    OperationTraitObject,
    ParameterObject,
    ParametersObject,
    ReferenceObject, RuntimeExpression, SchemaObject,
    SecurityRequirementObject, SecuritySchemeObject,
    ServerBindingsObject, ServerObject, ServerVariableObject, ServersObject, SpecObject,
    SpecObjectVisitor,
    TagObject, TagsObject,
)
from asynchron.codegen.spec.walker.base import Walker
from asynchron.codegen.spec.walker.spec_object_path import SpecObjectPath, SpecObjectWithPathWalker
from asynchron.serializable_object_modifier import SerializableObjectModifier


class SpecObjectTransformer(AsyncApiConfigTransformer):

    def __init__(
            self,
            transformer: t.Callable[[SpecObjectPath, SpecObject], SpecObject],
            modifier: t.Optional[SerializableObjectModifier] = None,
            walker: t.Optional[Walker[SpecObject, t.Tuple[SpecObjectPath, SpecObject]]] = None,
    ) -> None:
        self.__transformer = transformer
        self.__modifier = modifier or SerializableObjectModifier()
        self.__walker = walker or SpecObjectWithPathWalker.create_dfs_pre_ordering()

    def transform(self, config: AsyncAPIObject) -> AsyncAPIObject:
        changes: t.List[t.Tuple[t.Sequence[t.Union[int, str]], SpecObject]] = []

        for path, obj in self.__walker.walk(config):
            transformed_obj = self.__transformer(path, obj)
            if transformed_obj != obj:
                changes.append((path, transformed_obj))

        return self.__modifier.replace(config, changes)


class SpecObjectTitleNormalizer(SpecObjectVisitor[SpecObject]):

    def __init__(
            self,
            path: SpecObjectPath,
    ) -> None:
        self.__path = path

    def visit_identifier(self, obj: Identifier) -> Identifier:
        return obj

    def visit_runtime_expression(self, obj: RuntimeExpression) -> RuntimeExpression:
        return obj

    def visit_reference_object(self, obj: ReferenceObject) -> ReferenceObject:
        return obj

    def visit_schema_object(self, obj: SchemaObject) -> SchemaObject:
        return obj.copy(update={
            "title": self.__normalize_name_or_default(obj.title),
        })

    def visit_external_documentation_object(self, obj: ExternalDocumentationObject) -> ExternalDocumentationObject:
        return obj

    def visit_tag_object(self, obj: TagObject) -> TagObject:
        return obj

    def visit_tags_object(self, obj: TagsObject) -> TagsObject:
        return obj

    def visit_contact_object(self, obj: ContactObject) -> ContactObject:
        return obj

    def visit_license_object(self, obj: LicenseObject) -> LicenseObject:
        return obj

    def visit_info_object(self, obj: InfoObject) -> InfoObject:
        return obj.copy(update={
            "title": self.__normalize_name(obj.title),
        })

    def visit_server_bindings_object(self, obj: ServerBindingsObject) -> ServerBindingsObject:
        return obj

    def visit_security_requirement_object(self, obj: SecurityRequirementObject) -> SecurityRequirementObject:
        return obj

    def visit_server_variable_object(self, obj: ServerVariableObject) -> ServerVariableObject:
        return obj

    def visit_server_object(self, obj: ServerObject) -> ServerObject:
        return obj

    def visit_servers_object(self, obj: ServersObject) -> ServersObject:
        return obj

    def visit_default_content_type(self, obj: DefaultContentType) -> DefaultContentType:
        return obj

    def visit_correlation_id_object(self, obj: CorrelationIdObject) -> CorrelationIdObject:
        return obj

    def visit_message_bindings_object(self, obj: MessageBindingsObject) -> MessageBindingsObject:
        return obj

    def visit_message_example_object(self, obj: MessageExampleObject) -> MessageExampleObject:
        return obj

    def visit_message_trait_object(self, obj: MessageTraitObject) -> MessageTraitObject:
        return obj

    def visit_message_object(self, obj: MessageObject) -> MessageObject:
        return obj

    def visit_operation_bindings_object(self, obj: OperationBindingsObject) -> OperationBindingsObject:
        return obj

    def visit_operation_trait_object(self, obj: OperationTraitObject) -> OperationTraitObject:
        return obj

    def visit_operation_object(self, obj: OperationObject) -> OperationObject:
        return obj

    def visit_parameter_object(self, obj: ParameterObject) -> ParameterObject:
        return obj

    def visit_parameters_object(self, obj: ParametersObject) -> ParametersObject:
        return obj

    def visit_channel_bindings_object(self, obj: ChannelBindingsObject) -> ChannelBindingsObject:
        return obj

    def visit_channel_item_object(self, obj: ChannelItemObject) -> ChannelItemObject:
        return obj

    def visit_channels_object(self, obj: ChannelsObject) -> ChannelsObject:
        # TODO: remove commented code, it breaks the config
        # return obj.copy(update={"__root__": {
        #     self.__normalize_name(key): value
        #     for key, value in obj.__root__.items()
        # }})
        return obj

    def visit_oauth_flow_object(self, obj: OAuthFlowObject) -> OAuthFlowObject:
        return obj

    def visit_oauth_flows_object(self, obj: OAuthFlowsObject) -> OAuthFlowsObject:
        return obj

    def visit_security_scheme_object(self, obj: SecuritySchemeObject) -> SecuritySchemeObject:
        return obj

    def visit_components_object(self, obj: ComponentsObject) -> ComponentsObject:
        return obj

    def visit_async_api_object(self, obj: AsyncAPIObject) -> AsyncAPIObject:
        return obj

    def __normalize_name(self, *values: str) -> str:
        result = re.sub(r"[^A-Za-z0-9_]+", "_", "_".join(values))
        result = stringcase.snakecase(result) # type: ignore[misc]
        result = re.sub(r"_+", "_", result)
        result = re.sub(r"^_?(.*?)_$", "\1", result)

        return result

    def __normalize_name_or_default(self, value: t.Optional[str]) -> str:
        if value is not None:
            return self.__normalize_name(value)

        return self.__normalize_name(*(str(part) for part in self.__path))
