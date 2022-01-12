__all__ = (
    "Reference",
    "ReferencedSpecObject",
    "ReferencedDescendantSpecObjectVisitor",
)

import typing as t
from dataclasses import dataclass

from asynchron.codegen.spec.base import (
    AsyncAPIObject,
    ChannelBindingsObject,
    ChannelItemObject,
    ChannelsObject,
    ComponentsObject,
    ContactObject,
    CorrelationIdObject,
    DefaultContentType, ExternalDocumentationObject,
    Identifier, InfoObject,
    LicenseObject,
    MessageBindingsObject,
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
    ReferenceObject,
    RuntimeExpression, SchemaObject,
    SecurityRequirementObject,
    SecuritySchemeObject,
    ServerBindingsObject,
    ServerObject,
    ServerVariableObject,
    ServersObject,
    SpecObject,
    SpecObjectVisitor,
    TagObject,
    TagsObject,
)

Reference = t.Sequence[t.Union[int, str]]


@dataclass(frozen=True)
class ReferencedSpecObject:
    ref: Reference
    value: SpecObject


# noinspection PyTypeChecker
class ReferencedDescendantSpecObjectVisitor(SpecObjectVisitor[t.Sequence[ReferencedSpecObject]]):
    __EMPTY: t.Final[t.Sequence[ReferencedSpecObject]] = ()

    def visit_identifier(self, obj: Identifier) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_runtime_expression(self, obj: RuntimeExpression) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_reference_object(self, obj: ReferenceObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_schema_object(self, obj: SchemaObject) -> t.Sequence[ReferencedSpecObject]:
        return _ReferencedSpecObjectListBuilder() \
            .add(("prefixItems",), obj.prefix_items) \
            .add(("items",), obj.items) \
            .add(("additionalProperties",), obj.additional_properties) \
            .add(("patternProperties",), obj.pattern_properties) \
            .add(("oneOf",), obj.one_of) \
            .add(("anyOf",), obj.any_of) \
            .add(("allOf",), obj.all_of) \
            .add(("enum",), obj.enum) \
            .add(("properties",), obj.properties)

    def visit_external_documentation_object(
            self,
            obj: ExternalDocumentationObject,
    ) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_tag_object(self, obj: TagObject) -> t.Sequence[ReferencedSpecObject]:
        return _ReferencedSpecObjectListBuilder() \
            .add("externalDocs", obj.external_docs)

    def visit_tags_object(self, obj: TagsObject) -> t.Sequence[ReferencedSpecObject]:
        return _ReferencedSpecObjectListBuilder().add((), obj.__root__)

    def visit_contact_object(self, obj: ContactObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_license_object(self, obj: LicenseObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_info_object(self, obj: InfoObject) -> t.Sequence[ReferencedSpecObject]:
        return _ReferencedSpecObjectListBuilder() \
            .add(("contact",), obj.contact) \
            .add(("license",), obj.license)

    def visit_server_bindings_object(self, obj: ServerBindingsObject) -> t.Sequence[ReferencedSpecObject]:
        # TODO: maybe object of each protocol to the list
        return self.__EMPTY

    def visit_security_requirement_object(self, obj: SecurityRequirementObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_server_variable_object(self, obj: ServerVariableObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_server_object(self, obj: ServerObject) -> t.Sequence[ReferencedSpecObject]:
        return _ReferencedSpecObjectListBuilder() \
            .add(("variables",), obj.variables) \
            .add(("security",), obj.security) \
            .add(("bindings",), obj.bindings)

    def visit_servers_object(self, obj: ServersObject) -> t.Sequence[ReferencedSpecObject]:
        # FIXME: error: Argument 1 to "add" of "_ReferencedSpecObjectListBuilder" has incompatible type "Mapping[
        #  ServerName, ServerObject]"; expected "Optional[Mapping[str, Optional[ReferencedSpecObject]]]"  [arg-type]
        return _ReferencedSpecObjectListBuilder().add((), obj.__root__)

    def visit_default_content_type(self, obj: DefaultContentType) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_correlation_id_object(self, obj: CorrelationIdObject) -> t.Sequence[ReferencedSpecObject]:
        return _ReferencedSpecObjectListBuilder() \
            .add(("location",), obj.location)

    def visit_message_bindings_object(self, obj: MessageBindingsObject) -> t.Sequence[ReferencedSpecObject]:
        # TODO: maybe object of each protocol to the list,
        return self.__EMPTY

    def visit_message_example_object(self, obj: MessageExampleObject) -> t.Sequence[ReferencedSpecObject]:
        return _ReferencedSpecObjectListBuilder() \
            .add("payload", t.cast(object, obj.payload))

    def visit_message_trait_object(self, obj: MessageTraitObject) -> t.Sequence[ReferencedSpecObject]:
        return _ReferencedSpecObjectListBuilder() \
            .add(("headers",), obj.headers) \
            .add(("correlationId",), obj.correlation_id) \
            .add(("bindings",), obj.bindings) \
            .add(("examples",), obj.examples) \
            .add(("tags",), obj.tags) \
            .add(("externalDocs",), obj.external_docs)

    def visit_message_object(self, obj: MessageObject) -> t.Sequence[ReferencedSpecObject]:
        return _ReferencedSpecObjectListBuilder() \
            .add(("headers",), obj.headers) \
            .add(("correlationId",), obj.correlation_id) \
            .add(("bindings",), obj.bindings) \
            .add(("examples",), obj.examples) \
            .add(("payload",), obj.payload) \
            .add(("traits",), obj.traits) \
            .add(("tags",), obj.tags) \
            .add(("externalDocs",), obj.external_docs)

    def visit_operation_bindings_object(self, obj: OperationBindingsObject) -> t.Sequence[ReferencedSpecObject]:
        # TODO: maybe object of each protocol to the list
        return self.__EMPTY

    def visit_operation_trait_object(self, obj: OperationTraitObject) -> t.Sequence[ReferencedSpecObject]:
        return _ReferencedSpecObjectListBuilder() \
            .add(("bindings",), obj.bindings) \
            .add(("tags",), obj.tags) \
            .add(("externalDocs",), obj.external_docs)

    def visit_operation_object(self, obj: OperationObject) -> t.Sequence[ReferencedSpecObject]:
        result = _ReferencedSpecObjectListBuilder() \
            .add(("bindings",), obj.bindings) \
            .add(("traits",), obj.traits) \
            .add(("tags",), obj.tags) \
            .add(("externalDocs",), obj.external_docs) \
            .add(("message",), obj.message)

        return result

    def visit_parameter_object(self, obj: ParameterObject) -> t.Sequence[ReferencedSpecObject]:
        return _ReferencedSpecObjectListBuilder() \
            .add(("schema",), obj.schema_) \
            .add(("location",), obj.location)

    def visit_parameters_object(self, obj: ParametersObject) -> t.Sequence[ReferencedSpecObject]:
        # FIXME: error: Argument 1 to "add" of "_ReferencedSpecObjectListBuilder" has incompatible type "Mapping[
        #  ParameterName, Union[ParameterObject, ReferenceObject]]"; expected  "Optional[Mapping[str,
        #  Optional[ReferencedSpecObject]]]"  [arg-type]
        return _ReferencedSpecObjectListBuilder().add((), t.cast(t.Mapping[str, SpecObject], obj.__root__))

    def visit_channel_bindings_object(self, obj: ChannelBindingsObject) -> t.Sequence[ReferencedSpecObject]:
        # TODO: maybe object of each protocol to the list
        return self.__EMPTY

    def visit_channel_item_object(self, obj: ChannelItemObject) -> t.Sequence[ReferencedSpecObject]:
        return _ReferencedSpecObjectListBuilder() \
            .add(("subscribe",), obj.subscribe) \
            .add(("publish",), obj.publish) \
            .add(("parameters",), obj.parameters) \
            .add(("bindings",), obj.bindings)

    def visit_channels_object(self, obj: ChannelsObject) -> t.Sequence[ReferencedSpecObject]:
        return _ReferencedSpecObjectListBuilder().add((), obj.__root__)

    def visit_oauth_flow_object(self, obj: OAuthFlowObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_oauth_flows_object(self, obj: OAuthFlowsObject) -> t.Sequence[ReferencedSpecObject]:
        return _ReferencedSpecObjectListBuilder() \
            .add(("implicit",), obj.implicit) \
            .add(("password",), obj.password) \
            .add(("clientCredentials",), obj.client_credentials) \
            .add(("authorizationCode",), obj.authorization_code)

    def visit_security_scheme_object(self, obj: SecuritySchemeObject) -> t.Sequence[ReferencedSpecObject]:
        return _ReferencedSpecObjectListBuilder() \
            .add(("flows",), obj.flows)

    def visit_components_object(self, obj: ComponentsObject) -> t.Sequence[ReferencedSpecObject]:
        return _ReferencedSpecObjectListBuilder() \
            .add(("schemas",), obj.schemas) \
            .add(("messages",), obj.messages) \
            .add(("securitySchemes",), obj.security_schemes) \
            .add(("parameters",), obj.parameters) \
            .add(("correlationIds",), obj.correlation_ids) \
            .add(("operationTraits",), obj.operation_traits) \
            .add(("messageTraits",), obj.message_traits) \
            .add(("serverBindings",), obj.server_bindings) \
            .add(("channelBindings",), obj.channel_bindings) \
            .add(("operationBindings",), obj.operation_bindings) \
            .add(("messageBindings",), obj.message_bindings)

    def visit_async_api_object(self, obj: AsyncAPIObject) -> t.Sequence[ReferencedSpecObject]:
        return _ReferencedSpecObjectListBuilder() \
            .add(("info",), obj.info) \
            .add(("servers",), obj.servers) \
            .add(("channels",), obj.channels) \
            .add(("components",), obj.components) \
            .add(("tags",), obj.tags) \
            .add(("externalDocs",), obj.external_docs)


class _ReferencedSpecObjectListBuilder(t.Sequence[ReferencedSpecObject]):
    __slots__ = (
        "__items",
    )

    def __init__(self) -> None:
        self.__items: t.List[ReferencedSpecObject] = []

    @t.overload
    def __getitem__(self, i: int) -> ReferencedSpecObject:
        ...

    @t.overload
    def __getitem__(self, s: slice) -> t.Sequence[ReferencedSpecObject]:
        ...

    def __getitem__(self, i: t.Union[int, slice]) -> t.Union[ReferencedSpecObject, t.Sequence[ReferencedSpecObject]]:
        return self.__items.__getitem__(i)

    def index(self, value: ReferencedSpecObject, start: t.Optional[int] = None, stop: t.Optional[int] = None) -> int:
        return self.__items.index(value, t.cast(int, start if start is not None else ...),
                                  t.cast(int, stop if stop is not None else ...))

    def count(self, value: ReferencedSpecObject) -> int:
        return self.__items.count(value)

    def __contains__(self, x: object) -> bool:
        return x in self.__items

    def __iter__(self) -> t.Iterator[ReferencedSpecObject]:
        return iter(self.__items)

    def __reversed__(self) -> t.Iterator[ReferencedSpecObject]:
        return reversed(self.__items)

    def __len__(self) -> int:
        return len(self.__items)

    def add(
            self,
            ref: Reference,
            obj: t.Optional[t.Union[
                t.Optional[object],
                t.Sequence[t.Optional[object]],
                t.Mapping[str, t.Optional[object]],
            ]],
    ) -> "_ReferencedSpecObjectListBuilder":
        if obj is not None:
            if isinstance(obj, SpecObject):
                self.__items.append(ReferencedSpecObject(ref, obj))

            elif isinstance(obj, t.Sequence):
                for index, item in enumerate(t.cast(t.Sequence[object], obj)):
                    if isinstance(item, SpecObject):
                        self.__items.append(ReferencedSpecObject((*ref, index), item))

            elif isinstance(obj, t.Mapping):
                for key, item in t.cast(t.Mapping[object, object], obj).items():
                    if isinstance(key, str) and isinstance(item, SpecObject):
                        self.__items.append(ReferencedSpecObject((*ref, key), item))

        return self
