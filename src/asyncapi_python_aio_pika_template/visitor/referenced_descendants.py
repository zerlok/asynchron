__all__ = (
    "Reference",
    "ReferencedSpecObject",
    "ReferencedDescendantSpecObjectVisitor",
)

import typing as t
from dataclasses import dataclass

from asyncapi_python_aio_pika_template.spec import (
    AsyncAPIObject,
    ChannelBindingsObject,
    ChannelItemObject,
    ChannelsObject,
    ComponentName, ComponentsObject,
    ContactObject,
    CorrelationIdObject,
    DefaultContentType, Email,
    ExternalDocumentationObject,
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
    ParameterName, ParameterObject,
    ParametersObject,
    Protocol, ReferenceObject,
    RuntimeExpression, SchemaObject,
    SecurityRequirementObject,
    SecuritySchemeObject,
    SecuritySchemeType, SemanticVersion,
    ServerBindingsObject,
    ServerName, ServerObject,
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

    def visit_email(self, obj: Email) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_semantic_version(self, obj: SemanticVersion) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_identifier(self, obj: Identifier) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_runtime_expression(self, obj: RuntimeExpression) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_server_name(self, obj: ServerName) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_parameter_name(self, obj: ParameterName) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_component_name(self, obj: ComponentName) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_protocol(self, obj: Protocol) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_security_scheme_type(self, obj: SecuritySchemeType) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_reference_object(self, obj: ReferenceObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_schema_object(self, obj: SchemaObject) -> t.Sequence[ReferencedSpecObject]:
        # TODO: maybe return fields with `ReferenceObject`. Check it after `SchemaObject` is ready.
        return self.__EMPTY

    def visit_external_documentation_object(
            self,
            obj: ExternalDocumentationObject,
    ) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_tag_object(self, obj: TagObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_tags_object(self, obj: TagsObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__create_object_list().expand((), obj.__root__)

    def visit_contact_object(self, obj: ContactObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__create_object_list() \
            .add(("email",), obj.email)

    def visit_license_object(self, obj: LicenseObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_info_object(self, obj: InfoObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__create_object_list() \
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
        return self.__create_object_list() \
            .expand(("variables",), obj.variables) \
            .expand(("security",), obj.security) \
            .add(("bindings",), obj.bindings)

    def visit_servers_object(self, obj: ServersObject) -> t.Sequence[ReferencedSpecObject]:
        # FIXME: error: Argument 1 to "expand" of "_DescendantsListBuilder" has incompatible type "Mapping[
        #  ServerName, ServerObject]"; expected "Optional[Mapping[str, Optional[ReferencedSpecObject]]]"  [arg-type]
        return self.__create_object_list().expand((), obj.__root__)

    def visit_default_content_type(self, obj: DefaultContentType) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_correlation_id_object(self, obj: CorrelationIdObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__create_object_list() \
            .add(("location",), obj.location)

    def visit_message_bindings_object(self, obj: MessageBindingsObject) -> t.Sequence[ReferencedSpecObject]:
        # TODO: maybe object of each protocol to the list,
        return self.__EMPTY

    def visit_message_example_object(self, obj: MessageExampleObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_message_trait_object(self, obj: MessageTraitObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__create_object_list() \
            .add(("headers",), obj.headers) \
            .add(("correlationId",), obj.correlationId) \
            .add(("bindings",), obj.bindings) \
            .expand(("examples",), obj.examples)

    def visit_message_object(self, obj: MessageObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__create_object_list() \
            .add(("headers",), obj.headers) \
            .add(("correlationId",), obj.correlationId) \
            .add(("bindings",), obj.bindings) \
            .expand(("examples",), obj.examples) \
            .add(("payload",), obj.payload) \
            .expand(("traits",), obj.traits)

    def visit_operation_bindings_object(self, obj: OperationBindingsObject) -> t.Sequence[ReferencedSpecObject]:
        # TODO: maybe object of each protocol to the list
        return self.__EMPTY

    def visit_operation_trait_object(self, obj: OperationTraitObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__create_object_list() \
            .add(("bindings",), obj.bindings)

    def visit_operation_object(self, obj: OperationObject) -> t.Sequence[ReferencedSpecObject]:
        result = self.__create_object_list() \
            .add(("bindings",), obj.bindings) \
            .expand(("traits",), obj.traits)

        if isinstance(obj.message, (t.Sequence, t.Mapping)):
            result.expand(("message",), obj.message)

        else:
            result.add(("message",), obj.message)

        return result

    def visit_parameter_object(self, obj: ParameterObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__create_object_list() \
            .add(("schema",), obj.schema_) \
            .add(("location",), obj.location)

    def visit_parameters_object(self, obj: ParametersObject) -> t.Sequence[ReferencedSpecObject]:
        # FIXME: error: Argument 1 to "expand" of "_DescendantsListBuilder" has incompatible type "Mapping[
        #  ParameterName, Union[ParameterObject, ReferenceObject]]"; expected  "Optional[Mapping[str,
        #  Optional[ReferencedSpecObject]]]"  [arg-type]
        return self.__create_object_list().expand((), t.cast(t.Mapping[str, SpecObject], obj.__root__))

    def visit_channel_bindings_object(self, obj: ChannelBindingsObject) -> t.Sequence[ReferencedSpecObject]:
        # TODO: maybe object of each protocol to the list
        return self.__EMPTY

    def visit_channel_item_object(self, obj: ChannelItemObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__create_object_list() \
            .add(("subscribe",), obj.subscribe) \
            .add(("publish",), obj.publish) \
            .add(("parameters",), obj.parameters) \
            .add(("bindings",), obj.bindings)

    def visit_channels_object(self, obj: ChannelsObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__create_object_list().expand((), obj.__root__)

    def visit_oauth_flow_object(self, obj: OAuthFlowObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__EMPTY

    def visit_oauth_flows_object(self, obj: OAuthFlowsObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__create_object_list() \
            .add(("implicit",), obj.implicit) \
            .add(("password",), obj.password) \
            .add(("clientCredentials",), obj.clientCredentials) \
            .add(("authorizationCode",), obj.authorizationCode)

    def visit_security_scheme_object(self, obj: SecuritySchemeObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__create_object_list() \
            .add(("type",), obj.type_) \
            .add(("flows",), obj.flows)

    def visit_components_object(self, obj: ComponentsObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__create_object_list() \
            .expand(("schemas",), obj.schemas) \
            .expand(("messages",), obj.messages) \
            .expand(("securitySchemes",), obj.securitySchemes) \
            .expand(("parameters",), obj.parameters) \
            .expand(("correlationIds",), obj.correlationIds) \
            .expand(("operationTraits",), obj.operationTraits) \
            .expand(("messageTraits",), obj.messageTraits) \
            .expand(("serverBindings",), obj.serverBindings) \
            .expand(("channelBindings",), obj.channelBindings) \
            .expand(("operationBindings",), obj.operationBindings) \
            .expand(("messageBindings",), obj.messageBindings)

    def visit_async_api_object(self, obj: AsyncAPIObject) -> t.Sequence[ReferencedSpecObject]:
        return self.__create_object_list() \
            .add(("info",), obj.info) \
            .add(("servers",), obj.servers) \
            .add(("channels",), obj.channels) \
            .add(("components",), obj.components)

    def __create_object_list(self) -> "_DescendantsListBuilder":
        return _DescendantsListBuilder()


class _DescendantsListBuilder(t.Sequence[ReferencedSpecObject]):
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
            obj: t.Optional[SpecObject],
    ) -> "_DescendantsListBuilder":
        if obj is not None:
            self.__items.append(ReferencedSpecObject(ref, obj))

        return self

    @t.overload
    def expand(
            self,
            ref: Reference,
            objs: t.Optional[t.Sequence[t.Optional[SpecObject]]],
    ) -> "_DescendantsListBuilder":
        ...

    @t.overload
    def expand(
            self,
            ref: Reference,
            objs: t.Optional[t.Mapping[str, t.Optional[SpecObject]]],
    ) -> "_DescendantsListBuilder":
        ...

    def expand(
            self,
            ref: Reference,
            objs: t.Optional[t.Union[t.Sequence[t.Optional[SpecObject]], t.Mapping[str, t.Optional[SpecObject]]]],
    ) -> "_DescendantsListBuilder":
        if objs is not None:
            if isinstance(objs, t.Sequence):
                for index, item in enumerate(objs):
                    if item is not None:
                        self.__items.append(ReferencedSpecObject((*ref, index), item))

            elif isinstance(objs, t.Mapping):
                for key, item in objs.items():
                    if item is not None:
                        self.__items.append(ReferencedSpecObject((*ref, key), item))

            else:
                raise TypeError("Invalid objects type", type(objs))

        return self
