__all__ = (
    "DescendantsSpecObjectVisitor",
)

import typing as t

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

T = t.TypeVar("T")


# noinspection PyTypeChecker
class DescendantsSpecObjectVisitor(SpecObjectVisitor[t.Sequence[t.Tuple[str, SpecObject]]]):
    __EMPTY: t.Final[t.Sequence[t.Tuple[str, SpecObject]]] = ()

    def visit_email(self, obj: Email) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_semantic_version(self, obj: SemanticVersion) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_identifier(self, obj: Identifier) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_runtime_expression(self, obj: RuntimeExpression) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_server_name(self, obj: ServerName) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_parameter_name(self, obj: ParameterName) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_component_name(self, obj: ComponentName) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_protocol(self, obj: Protocol) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_security_scheme_type(self, obj: SecuritySchemeType) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_reference_object(self, obj: ReferenceObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_schema_object(self, obj: SchemaObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_external_documentation_object(
            self,
            obj: ExternalDocumentationObject,
    ) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_tag_object(self, obj: TagObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_tags_object(self, obj: TagsObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_contact_object(self, obj: ContactObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_license_object(self, obj: LicenseObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_info_object(self, obj: InfoObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_server_bindings_object(self, obj: ServerBindingsObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_server_variable_object(self, obj: ServerVariableObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_security_requirement_object(self, obj: SecurityRequirementObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_server_object(self, obj: ServerObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_servers_object(self, obj: ServersObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_default_content_type(self, obj: DefaultContentType) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_correlation_id_object(self, obj: CorrelationIdObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_message_bindings_object(self, obj: MessageBindingsObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_message_example_object(self, obj: MessageExampleObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_message_trait_object(self, obj: MessageTraitObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_message_object(self, obj: MessageObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_operation_bindings_object(self, obj: OperationBindingsObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_operation_trait_object(self, obj: OperationTraitObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        raise NotImplementedError

    def visit_operation_object(self, obj: OperationObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        # TODO: find out how to create a list of traits and messages (sequences)
        return self.__create_object_list()

    def visit_parameter_object(self, obj: ParameterObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        return self.__create_object_list() \
            .add("schema", obj.schema_) \
            .add("location", obj.location)

    def visit_parameters_object(self, obj: ParametersObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        return self.__create_object_list().expand(obj)

    def visit_channel_bindings_object(self, obj: ChannelBindingsObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        return self.__create_object_list() \
            .add("http", obj.http) \
            .add("amqp", obj.amqp)

    def visit_channel_item_object(self, obj: ChannelItemObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        return self.__create_object_list() \
            .add("subscribe", obj.subscribe) \
            .add("publish", obj.publish) \
            .add("parameters", obj.parameters) \
            .add("bindings", obj.bindings)

    def visit_channels_object(self, obj: ChannelsObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        return self.__create_object_list().expand(obj)

    def visit_oauth_flow_object(self, obj: OAuthFlowObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        return self.__create_object_list() \
            .add("authorizationUrl", obj.authorizationUrl) \
            .add("tokenUrl", obj.tokenUrl) \
            .add("refreshUrl", obj.refreshUrl) \
            .add("scopes", obj.scopes)

    def visit_oauth_flows_object(self, obj: OAuthFlowsObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        return self.__create_object_list() \
            .add("implicit", obj.implicit) \
            .add("password", obj.password) \
            .add("clientCredentials", obj.clientCredentials) \
            .add("authorizationCode", obj.authorizationCode)

    def visit_security_scheme_object(self, obj: SecuritySchemeObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        return self.__create_object_list() \
            .add("type", obj.type_) \
            .add("flows", obj.flows)

    def visit_components_object(self, obj: ComponentsObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        return self.__create_object_list() \
            .expand(obj.schemas) \
            .expand(obj.messages) \
            .expand(obj.securitySchemes) \
            .expand(obj.parameters) \
            .expand(obj.correlationIds) \
            .expand(obj.operationTraits) \
            .expand(obj.messageTraits) \
            .expand(obj.serverBindings) \
            .expand(obj.channelBindings) \
            .expand(obj.operationBindings) \
            .expand(obj.messageBindings)

    def visit_async_api_object(self, obj: AsyncAPIObject) -> t.Sequence[t.Tuple[str, SpecObject]]:
        return self.__create_object_list() \
            .add("info", obj.info) \
            .add("servers", obj.servers) \
            .add("channels", obj.channels) \
            .add("components", obj.components)

    def __create_object_list(self) -> "_NonNoneItemListBuilder[SpecObject]":
        return _NonNoneItemListBuilder[SpecObject]()


class _NonNoneItemListBuilder(t.Sequence[t.Tuple[str, T]]):

    def __init__(self) -> None:
        self.__items: t.List[t.Tuple[str, T]] = []

    @t.overload
    def __getitem__(self, i: int) -> t.Tuple[str, T]:
        ...

    @t.overload
    def __getitem__(self, s: slice) -> t.Sequence[t.Tuple[str, T]]:
        ...

    def __getitem__(self, i: t.Union[int, slice]) -> t.Union[t.Tuple[str, T], t.Sequence[t.Tuple[str, T]]]:
        return self.__items.__getitem__(i)

    def index(self, value: t.Tuple[str, T], start: t.Optional[int] = None, stop: t.Optional[int] = None) -> int:
        return self.__items.index(value, t.cast(int, start if start is not None else ...),
                                  t.cast(int, stop if stop is not None else ...))

    def count(self, value: t.Tuple[str, T]) -> int:
        return self.__items.count(value)

    def __contains__(self, x: object) -> bool:
        return x in self.__items

    def __iter__(self) -> t.Iterator[t.Tuple[str, T]]:
        return iter(self.__items)

    def __reversed__(self) -> t.Iterator[t.Tuple[str, T]]:
        return reversed(self.__items)

    def __len__(self) -> int:
        return len(self.__items)

    @t.overload
    def add(self, key: str, obj: T) -> "_NonNoneItemListBuilder[T]":
        ...

    @t.overload
    def add(self, key: str, obj: t.Optional[T]) -> "_NonNoneItemListBuilder[T]":
        ...

    def add(self, key: str, obj: t.Optional[T]) -> "_NonNoneItemListBuilder[T]":
        if obj is not None:
            self.__items.append((key, obj))

        return self

    def expand(self, objs: t.Optional[t.Mapping[str, t.Optional[T]]]) -> "_NonNoneItemListBuilder[T]":
        if objs is not None:
            for key, value in objs.items():
                if value is not None:
                    self.__items.append((key, value))

        return self
