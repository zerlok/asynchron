__all__ = (
    "DescendantsSpecObjectVisitor",
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
    MessageExamplesObject, MessageObject,
    MessageTraitObject,
    MessageTraitsObject, MessagesObject, OAuthFlowObject,
    OAuthFlowsObject,
    OperationBindingsObject,
    OperationObject,
    OperationTraitObject,
    OperationTraitsObject, ParameterName, ParameterObject,
    ParametersObject,
    Protocol, ReferenceObject,
    RuntimeExpression, SchemaObject,
    SecurityRequirementObject,
    SecurityRequirementsObject, SecuritySchemeObject,
    SecuritySchemeType, SemanticVersion,
    ServerBindingsObject,
    ServerName, ServerObject,
    ServerVariableObject,
    ServerVariablesObject, ServersObject,
    SpecObject,
    SpecObjectVisitor,
    TagObject,
    TagsObject,
)

T = t.TypeVar("T")


@dataclass(frozen=True)
class Descendant(t.Generic[T]):
    key: t.Union[int, str]
    value: T
    ancestor: t.Optional[T]


# noinspection PyTypeChecker
class DescendantsSpecObjectVisitor(SpecObjectVisitor[t.Sequence[Descendant[SpecObject]]]):
    __EMPTY: t.Final[t.Sequence[Descendant[SpecObject]]] = ()

    def visit_email(self, obj: Email) -> t.Sequence[Descendant[SpecObject]]:
        return self.__EMPTY

    def visit_semantic_version(self, obj: SemanticVersion) -> t.Sequence[Descendant[SpecObject]]:
        return self.__EMPTY

    def visit_identifier(self, obj: Identifier) -> t.Sequence[Descendant[SpecObject]]:
        return self.__EMPTY

    def visit_runtime_expression(self, obj: RuntimeExpression) -> t.Sequence[Descendant[SpecObject]]:
        return self.__EMPTY

    def visit_server_name(self, obj: ServerName) -> t.Sequence[Descendant[SpecObject]]:
        return self.__EMPTY

    def visit_parameter_name(self, obj: ParameterName) -> t.Sequence[Descendant[SpecObject]]:
        return self.__EMPTY

    def visit_component_name(self, obj: ComponentName) -> t.Sequence[Descendant[SpecObject]]:
        return self.__EMPTY

    def visit_protocol(self, obj: Protocol) -> t.Sequence[Descendant[SpecObject]]:
        return self.__EMPTY

    def visit_security_scheme_type(self, obj: SecuritySchemeType) -> t.Sequence[Descendant[SpecObject]]:
        return self.__EMPTY

    def visit_reference_object(self, obj: ReferenceObject) -> t.Sequence[Descendant[SpecObject]]:
        return self.__EMPTY

    def visit_schema_object(self, obj: SchemaObject) -> t.Sequence[Descendant[SpecObject]]:
        # TODO: maybe return fields with `ReferenceObject`. Check it after `SchemaObject` is ready.
        return self.__EMPTY

    def visit_external_documentation_object(
            self,
            obj: ExternalDocumentationObject,
    ) -> t.Sequence[Descendant[SpecObject]]:
        return self.__EMPTY

    def visit_tag_object(self, obj: TagObject) -> t.Sequence[Descendant[SpecObject]]:
        return self.__EMPTY

    def visit_tags_object(self, obj: TagsObject) -> t.Sequence[Descendant[SpecObject]]:
        # FIXME: find out how to pass `__root__` type for mypy
        return self.__create_object_list(obj).expand(obj)  # type: ignore

    def visit_contact_object(self, obj: ContactObject) -> t.Sequence[Descendant[SpecObject]]:
        return self.__create_object_list(obj) \
            .add("email", obj.email)

    def visit_license_object(self, obj: LicenseObject) -> t.Sequence[Descendant[SpecObject]]:
        return self.__EMPTY

    def visit_info_object(self, obj: InfoObject) -> t.Sequence[Descendant[SpecObject]]:
        return self.__create_object_list(obj) \
            .add("contact", obj.contact) \
            .add("license", obj.license)

    def visit_server_bindings_object(self, obj: ServerBindingsObject) -> t.Sequence[Descendant[SpecObject]]:
        # TODO: maybe object of each protocol to the list
        return self.__EMPTY

    def visit_security_requirement_object(self, obj: SecurityRequirementObject) -> t.Sequence[Descendant[SpecObject]]:
        return self.__EMPTY

    def visit_security_requirements_object(self, obj: SecurityRequirementsObject) -> t.Sequence[Descendant[SpecObject]]:
        # FIXME: find out how to pass `__root__` type for mypy
        return self.__create_object_list(obj).expand(obj)  # type: ignore

    def visit_server_variable_object(self, obj: ServerVariableObject) -> t.Sequence[Descendant[SpecObject]]:
        return self.__EMPTY

    def visit_server_variables_object(self, obj: ServerVariablesObject) -> t.Sequence[Descendant[SpecObject]]:
        # FIXME: find out how to pass `__root__` type for mypy
        return self.__create_object_list(obj).expand(obj)  # type: ignore

    def visit_server_object(self, obj: ServerObject) -> t.Sequence[Descendant[SpecObject]]:
        return self.__create_object_list(obj) \
            .add("protocol", obj.protocol) \
            .add("variables", obj.variables) \
            .add("security", obj.security) \
            .add("bindings", obj.bindings)

    def visit_servers_object(self, obj: ServersObject) -> t.Sequence[Descendant[SpecObject]]:
        # FIXME: find out how to pass `__root__` type for mypy
        return self.__create_object_list(obj).expand(obj)  # type: ignore

    def visit_default_content_type(self, obj: DefaultContentType) -> t.Sequence[Descendant[SpecObject]]:
        return self.__EMPTY

    def visit_correlation_id_object(self, obj: CorrelationIdObject) -> t.Sequence[Descendant[SpecObject]]:
        return self.__create_object_list(obj) \
            .add("location", obj.location)

    def visit_message_bindings_object(self, obj: MessageBindingsObject) -> t.Sequence[Descendant[SpecObject]]:
        # TODO: maybe object of each protocol to the list
        return self.__EMPTY

    def visit_message_example_object(self, obj: MessageExampleObject) -> t.Sequence[Descendant[SpecObject]]:
        return self.__EMPTY

    def visit_message_examples_object(self, obj: MessageExamplesObject) -> t.Sequence[Descendant[SpecObject]]:
        # FIXME: find out how to pass `__root__` type for mypy
        return self.__create_object_list(obj).expand(obj)  # type: ignore

    def visit_message_trait_object(self, obj: MessageTraitObject) -> t.Sequence[Descendant[SpecObject]]:
        return self.__create_object_list(obj) \
            .add("headers", obj.headers) \
            .add("correlationId", obj.correlationId) \
            .add("bindings", obj.bindings) \
            .add("examples", obj.examples)

    def visit_message_traits_object(self, obj: MessageTraitsObject) -> t.Sequence[Descendant[SpecObject]]:
        # FIXME: find out how to pass `__root__` type for mypy
        return self.__create_object_list(obj).expand(obj)  # type: ignore

    def visit_message_object(self, obj: MessageObject) -> t.Sequence[Descendant[SpecObject]]:
        return self.__create_object_list(obj) \
            .add("headers", obj.headers) \
            .add("correlationId", obj.correlationId) \
            .add("bindings", obj.bindings) \
            .add("examples", obj.examples) \
            .add("traits", obj.traits)

    def visit_messages_object(self, obj: MessagesObject) -> t.Sequence[Descendant[SpecObject]]:
        # FIXME: find out how to pass `__root__` type for mypy
        return self.__create_object_list(obj).expand(obj)  # type: ignore

    def visit_operation_bindings_object(self, obj: OperationBindingsObject) -> t.Sequence[Descendant[SpecObject]]:
        # TODO: maybe object of each protocol to the list
        return self.__EMPTY

    def visit_operation_trait_object(self, obj: OperationTraitObject) -> t.Sequence[Descendant[SpecObject]]:
        return self.__create_object_list(obj) \
            .add("bindings", obj.bindings)

    def visit_operation_traits_object(self, obj: OperationTraitsObject) -> t.Sequence[Descendant[SpecObject]]:
        # FIXME: find out how to pass `__root__` type for mypy
        return self.__create_object_list(obj).expand(obj)  # type: ignore

    def visit_operation_object(self, obj: OperationObject) -> t.Sequence[Descendant[SpecObject]]:
        # TODO: find out how to create a list of traits and messages (sequences)
        return self.__create_object_list(obj) \
            .add("bindings", obj.bindings) \
            .add("traits", obj.traits)

    def visit_parameter_object(self, obj: ParameterObject) -> t.Sequence[Descendant[SpecObject]]:
        return self.__create_object_list(obj) \
            .add("schema", obj.schema_) \
            .add("location", obj.location)

    def visit_parameters_object(self, obj: ParametersObject) -> t.Sequence[Descendant[SpecObject]]:
        # FIXME: find out how to pass `__root__` type for mypy
        return self.__create_object_list(obj).expand(obj)  # type: ignore

    def visit_channel_bindings_object(self, obj: ChannelBindingsObject) -> t.Sequence[Descendant[SpecObject]]:
        # TODO: maybe object of each protocol to the list
        return self.__EMPTY

    def visit_channel_item_object(self, obj: ChannelItemObject) -> t.Sequence[Descendant[SpecObject]]:
        return self.__create_object_list(obj) \
            .add("subscribe", obj.subscribe) \
            .add("publish", obj.publish) \
            .add("parameters", obj.parameters) \
            .add("bindings", obj.bindings)

    def visit_channels_object(self, obj: ChannelsObject) -> t.Sequence[Descendant[SpecObject]]:
        # FIXME: find out how to pass `__root__` type for mypy
        return self.__create_object_list(obj).expand(obj)  # type: ignore

    def visit_oauth_flow_object(self, obj: OAuthFlowObject) -> t.Sequence[Descendant[SpecObject]]:
        return self.__EMPTY

    def visit_oauth_flows_object(self, obj: OAuthFlowsObject) -> t.Sequence[Descendant[SpecObject]]:
        return self.__create_object_list(obj) \
            .add("implicit", obj.implicit) \
            .add("password", obj.password) \
            .add("clientCredentials", obj.clientCredentials) \
            .add("authorizationCode", obj.authorizationCode)

    def visit_security_scheme_object(self, obj: SecuritySchemeObject) -> t.Sequence[Descendant[SpecObject]]:
        return self.__create_object_list(obj) \
            .add("type", obj.type_) \
            .add("flows", obj.flows)

    def visit_components_object(self, obj: ComponentsObject) -> t.Sequence[Descendant[SpecObject]]:
        return self.__create_object_list(obj) \
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

    def visit_async_api_object(self, obj: AsyncAPIObject) -> t.Sequence[Descendant[SpecObject]]:
        return self.__create_object_list(obj) \
            .add("info", obj.info) \
            .add("servers", obj.servers) \
            .add("channels", obj.channels) \
            .add("components", obj.components)

    def __create_object_list(self, ancestor: t.Optional[SpecObject]) -> "_VisitedItemListBuilder[SpecObject]":
        return _VisitedItemListBuilder[SpecObject](ancestor)


class _VisitedItemListBuilder(t.Sequence[Descendant[T]]):
    __slots__ = (
        "__ancestor",
        "__items",
    )

    def __init__(self, ancestor: t.Optional[T]) -> None:
        self.__ancestor = ancestor
        self.__items: t.List[Descendant[T]] = []

    @t.overload
    def __getitem__(self, i: int) -> Descendant[T]:
        ...

    @t.overload
    def __getitem__(self, s: slice) -> t.Sequence[Descendant[T]]:
        ...

    def __getitem__(self, i: t.Union[int, slice]) -> t.Union[Descendant[T], t.Sequence[Descendant[T]]]:
        return self.__items.__getitem__(i)

    def index(self, value: Descendant[T], start: t.Optional[int] = None, stop: t.Optional[int] = None) -> int:
        return self.__items.index(value, t.cast(int, start if start is not None else ...),
                                  t.cast(int, stop if stop is not None else ...))

    def count(self, value: Descendant[T]) -> int:
        return self.__items.count(value)

    def __contains__(self, x: object) -> bool:
        return x in self.__items

    def __iter__(self) -> t.Iterator[Descendant[T]]:
        return iter(self.__items)

    def __reversed__(self) -> t.Iterator[Descendant[T]]:
        return reversed(self.__items)

    def __len__(self) -> int:
        return len(self.__items)

    def add(self, key: t.Union[int, str], obj: t.Optional[T]) -> "_VisitedItemListBuilder[T]":
        if obj is not None:
            self.__items.append(Descendant(key, obj, self.__ancestor))

        return self

    @t.overload
    def expand(self, objs: t.Optional[t.Sequence[t.Optional[T]]]) -> "_VisitedItemListBuilder[T]":
        ...

    @t.overload
    def expand(self, objs: t.Optional[t.Mapping[str, t.Optional[T]]]) -> "_VisitedItemListBuilder[T]":
        ...

    def expand(
            self,
            objs: t.Optional[t.Union[t.Sequence[t.Optional[T]], t.Mapping[str, t.Optional[T]]]],
    ) -> "_VisitedItemListBuilder[T]":
        if objs is not None:
            items: t.Iterable[t.Tuple[t.Union[int, str], t.Optional[T]]]
            if isinstance(objs, t.Sequence):
                items = enumerate(objs)
            elif isinstance(objs, t.Mapping):
                items = objs.items()
            else:
                raise TypeError("Invalid objects type", type(objs))

            for key, value in items:
                self.add(key, value)

        return self
