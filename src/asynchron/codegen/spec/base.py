__all__ = (
    "Validator",
    "StringRegexValidator",
    "Email",
    "SemanticVersion",
    "Identifier",
    "RuntimeExpression",
    "ServerName",
    "ParameterName",
    "ComponentName",
    "Protocol",
    "SecuritySchemeType",
    "SpecObject",
    "ReferenceObject",
    "SchemaObjectType",
    "SchemaObject",
    "HTTPBindingTrait",
    "AMQPBindingTrait",
    "ExternalDocumentationObject",
    "TagObject",
    "TagsObject",
    "ContactObject",
    "LicenseObject",
    "InfoObject",
    "ServerBindingsObject",
    "ServerVariableObject",
    "SecurityRequirementObject",
    "ServerObject",
    "ServersObject",
    "DefaultContentType",
    "CorrelationIdObject",
    "MessageBindingsObject",
    "MessageExampleObject",
    "MessageTraitObject",
    "MessageObject",
    "OperationBindingsObject",
    "OperationTraitObject",
    "OperationObject",
    "ParameterObject",
    "ParametersObject",
    "ChannelBindingsObject",
    "ChannelItemObject",
    "ChannelsObject",
    "OAuthFlowObject",
    "OAuthFlowsObject",
    "SecuritySchemeObject",
    "ComponentsObject",
    "AsyncAPIObject",
    "SpecObjectVisitor",
)

import abc
import re
import typing as t

from pydantic import AnyUrl, BaseModel, Field, HttpUrl

from asynchron.strict_typing import as_

T = t.TypeVar("T")
T_co = t.TypeVar("T_co", covariant=True)


class _BaseModel(BaseModel):
    class Config:
        allow_mutation = False


class SpecObject(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        raise NotImplementedError


class Validator(metaclass=abc.ABCMeta):

    @classmethod
    def __get_validators__(cls: t.Type[T]) -> t.Iterable[t.Callable[[t.Any], T]]:
        yield t.cast(t.Callable[[t.Any], T], t.cast(Validator, cls).validate)

    @classmethod
    @abc.abstractmethod
    def validate(cls: t.Type[T], value: t.Any) -> T:
        raise NotImplementedError


class StringRegexValidator(str, Validator):
    _PATTERN: t.ClassVar[t.Pattern[str]]

    def __init_subclass__(cls, pattern: t.Optional[t.Pattern[str]] = None) -> None:
        super().__init_subclass__()
        cls._PATTERN = pattern if pattern is not None else cls._PATTERN

    @classmethod
    def validate(cls: t.Type[T], value: t.Any) -> T:
        cls_ = t.cast(t.Type[StringRegexValidator], cls)

        if not isinstance(value, str):
            raise TypeError("Unexpected type", value)

        # noinspection PyProtectedMember
        if not cls_._PATTERN.match(value):
            raise ValueError(f"Invalid {cls.__name__} value", value)

        return t.cast(T, cls_(value))


class Email(StringRegexValidator, pattern=re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")):
    """
    An email string.

    https://emailregex.com/
    """


class SemanticVersion(StringRegexValidator):
    """
    A valid semantic version type.

    https://semver.org

    Regex was taken from https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
    """

    _PATTERN: t.ClassVar[t.Pattern[str]] = re.compile(r"^"
                                                      r"(?P<major>0|[1-9]\d*)"
                                                      r"\.(?P<minor>0|[1-9]\d*)"
                                                      r"\.(?P<patch>0|[1-9]\d*)"
                                                      r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
                                                      r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
                                                      r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"
                                                      r"$""")


class Identifier(StringRegexValidator, SpecObject):
    """
    This field represents a unique universal identifier of the application the AsyncAPI document is defining. It must
    conform to the URI format, according to RFC3986. It is RECOMMENDED to use a URN to globally and uniquely identify
    the application during long periods of time, even after it becomes unavailable or ceases to exist.

    https://www.asyncapi.com/docs/specifications/v2.2.0#A2SIdString
    """

    _PATTERN: t.ClassVar[t.Pattern[str]] = re.compile(r"^urn:[a-z0-9][a-z0-9-]{0,31}:[a-z0-9()+,\-.:=@;$_!*'%/?#]+$")

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_identifier(self)


class RuntimeExpression(str, SpecObject):
    """A runtime expression allows values to be defined based on information that will be available within the
    message. This mechanism is used by Correlation ID Object.

    The runtime expression is defined by the following [ABNF](https://tools.ietf.org/html/rfc5234) syntax:
    ```
    expression = ( "$message" "." source )
    source = ( header-reference | payload-reference )
    header-reference = "header" ["#" fragment]
    payload-reference = "payload" ["#" fragment]
    fragment = a JSON Pointer [RFC 6901](https://tools.ietf.org/html/rfc6901)
    ```

    https://www.asyncapi.com/docs/specifications/v2.2.0#runtimeExpression
    """

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_runtime_expression(self)


class ServerName(StringRegexValidator, pattern=re.compile(r"^[A-Za-z0-9_\-]+$")):
    pass


class ParameterName(StringRegexValidator, pattern=re.compile(r"^[A-Za-z0-9_\-]+$")):
    pass


class ComponentName(StringRegexValidator, pattern=re.compile(r"^[a-zA-Z0-9.\-_]+$")):
    pass


Protocol = t.Literal["amqp", "amqps", "http", "https", "ibmmq", "jms", "kafka", "kafka-secure", "anypointmq", "mqtt",
                     "secure-mqtt", "stomp", "stomps", "ws", "wss", "mercure"]

SecuritySchemeType = t.Literal["userPassword", "apiKey", "X509", "symmetricEncryption", "asymmetricEncryption",
                               "httpApiKey", "http", "oauth2", "openIdConnect", "plain", "scramSha256", "scramSha512",
                               "gssapi"]


class ReferenceObject(SpecObject, _BaseModel):
    """
    A simple object to allow referencing other components in the specification, internally and externally. The
    Reference Object is defined by <a href="https://tools.ietf.org/html/draft-pbryan-zyp-json-ref-03">JSON
    Reference</a> and follows the same structure, behavior and rules. A JSON Reference SHALL only be used to refer to
    a schema that is formatted in either JSON or YAML. In the case of a YAML-formatted Schema, the JSON Reference
    SHALL be applied to the JSON representation of that schema. The JSON representation SHALL be made by applying the
    conversion described here. For this specification, reference resolution is done as defined by the JSON Reference
    specification and not by the JSON Schema specification.

    https://www.asyncapi.com/docs/specifications/v2.2.0#referenceObject
    """

    class Config:
        schema_extra: t.ClassVar[t.Mapping[str, t.Any]] = {
            "examples": [
                {
                    "$ref": "#/components/schemas/Pet",
                },
            ],
        }

    ref: str = Field(
        alias="$ref",
        description="""Required. The reference string.""",
        regex=r"^#\S+$",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_reference_object(self)


# TODO: use it wth specification extension
class SpecificationExtensionKey(StringRegexValidator, pattern=re.compile(r"^x-[A-Za-z0-9._-]")):
    pass


class _WithSpecificationExtension(_BaseModel):
    """
    https://www.asyncapi.com/docs/specifications/v2.2.0#specificationExtensions
    """

    # TODO: add validator __root__: t.Mapping[SpecificationExtensionKey, t.Any] # -- raises ValueError: __root__
    #  cannot be mixed with other fields

    # class Config:
    #     extra = Extra.allow


class _WithDescriptionField(_BaseModel):
    description: t.Optional[str] = Field(
        description="""A short description of the application. <a href="https://spec.commonmark.org/">CommonMark 
        syntax</a> can be used for rich text representation.""",
    )


SchemaObjectType = t.Literal["null", "boolean", "number", "string", "array", "object", "integer"]


class SchemaObject(_WithSpecificationExtension, _WithDescriptionField, SpecObject, _BaseModel):
    """
    The Schema Object allows the definition of input and output data types. These types can be objects,
    but also primitives and arrays. This object is a superset of the JSON Schema Specification Draft 07. The empty
    schema (which allows any instance to validate) MAY be represented by the boolean value true and a schema which
    allows no instance to validate MAY be represented by the boolean value false. Further information about the
    properties can be found in JSON Schema Core and JSON Schema Validation. Unless stated otherwise, the property
    definitions follow the JSON Schema specification as referenced here.

    https://www.asyncapi.com/docs/specifications/v2.2.0#schemaObject
    """

    # Implementation was adapted from
    # https://github.com/koxudaxi/datamodel-code-generator/blob/513988f6391497b3c272801cd0f52941ec0178cb/datamodel_code_generator/parser/jsonschema.py#L115

    prefix_items: t.Optional[t.Union[bool, ReferenceObject, "SchemaObject", t.Sequence[t.Union[ReferenceObject, "SchemaObject"]]]] \
        = Field(
        default=None,
        alias="prefixItems",
    )
    items: t.Optional[t.Union[bool, ReferenceObject, "SchemaObject", t.Sequence[t.Union[ReferenceObject, "SchemaObject"]]]] \
        = Field(
        default=None,
        alias="items",
    )
    unique_items: t.Optional[bool] = Field(
        default=None,
        alias="uniqueItems",
    )
    type_: t.Optional[t.Union[SchemaObjectType, t.Sequence[SchemaObjectType]]] = Field(
        default=None,
        alias="type",
    )
    format_: t.Optional[str] = Field(
        default=None,
        alias="format",
    )
    pattern: t.Optional[str] = Field(
        default=None,
        alias="pattern",
    )
    min_length: t.Optional[int] = Field(
        default=None,
        alias="minLength",
    )
    max_length: t.Optional[int] = Field(
        default=None,
        alias="maxLength",
    )
    minimum: t.Optional[float] = Field(
        default=None,
        alias="minimum",
    )
    maximum: t.Optional[float] = Field(
        default=None,
        alias="maximum",
    )
    min_items: t.Optional[int] = Field(
        default=None,
        alias="minItems",
    )
    max_items: t.Optional[int] = Field(
        default=None,
        alias="maxItems",
    )
    multiple_of: t.Optional[float] = Field(
        default=None,
        alias="multipleOf",
    )
    exclusive_maximum: t.Optional[t.Union[float, bool]] = Field(
        default=None,
        alias="exclusiveMaximum",
    )
    exclusive_minimum: t.Optional[t.Union[float, bool]] = Field(
        default=None,
        alias="exclusiveMinimum",
    )
    additional_properties: t.Optional[t.Union[ReferenceObject, "SchemaObject", bool]] = Field(
        default=None,
        alias="additionalProperties",
    )
    pattern_properties: t.Optional[t.Mapping[str, t.Union[ReferenceObject, "SchemaObject"]]] = Field(
        default=None,
        alias="patternProperties",
    )
    one_of: t.Optional[t.Sequence[t.Union[ReferenceObject, "SchemaObject"]]] = Field(
        default=None,
        alias="oneOf",
    )
    any_of: t.Optional[t.Sequence[t.Union[ReferenceObject, "SchemaObject"]]] = Field(
        default=None,
        alias="anyOf",
    )
    all_of: t.Optional[t.Sequence[t.Union[ReferenceObject, "SchemaObject"]]] = Field(
        default=None,
        alias="allOf",
    )
    enum: t.Optional[t.Sequence[t.Union[ReferenceObject, "SchemaObject", t.Any]]] = Field(
        default=None,
        alias="enum",
    )
    write_only: t.Optional[bool] = Field(
        default=None,
        alias="writeOnly",
    )
    properties: t.Optional[t.Mapping[str, t.Union[ReferenceObject, "SchemaObject"]]] = Field(
        default=None,
        alias="properties",
    )
    required: t.Optional[t.Sequence[str]] = Field(
        default=None,
        alias="required",
    )
    nullable: t.Optional[bool] = Field(
        default=None,
        alias="nullable",
    )
    x_enum_var_names: t.Optional[t.Sequence[str]] = Field(
        default=None,
        alias="x-enum-varnames",
    )
    title: t.Optional[str] = Field(
        default=None,
        alias="title",
    )
    example: t.Optional[t.Any] = Field(
        default=None,
        alias="example",
    )
    examples: t.Optional[t.Any] = Field(
        default=None,
        alias="examples",
    )
    default: t.Optional[t.Any] = Field(
        default=None,
        alias="default",
    )
    schema_: t.Optional[AnyUrl] = Field(
        default=None,
        alias="$schema",
    )
    id_: t.Optional[str] = Field(
        default=None,
        alias="$id",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_schema_object(self)


# Fixes pydantic.errors.ConfigError: field "properties" not yet prepared so type is still a ForwardRef,
# you might need to call SchemaObject.update_forward_refs().
SchemaObject.update_forward_refs()


class _WithBindingVersion(_BaseModel):
    binding_version: t.Optional[str] = Field(
        alias="bindingVersion",
        description="""The version of this binding. If omitted, "latest" MUST be assumed.""",
    )


class HTTPBindingTrait:
    """
    https://github.com/asyncapi/bindings/blob/master/http/README.md
    """

    class HTTPServerBindingObject(_BaseModel):
        """This object MUST NOT contain any properties. Its name is reserved for future use."""
        __root__: None

    class HTTPChannelBindingObject(_BaseModel):
        """This object MUST NOT contain any properties. Its name is reserved for future use."""
        __root__: None

    class HTTPOperationBindingObject(_WithBindingVersion, _BaseModel):
        type_: t.Literal["request", "response"] = Field(
            title="type",
            description="""Required. Type of operation. Its value MUST be either request or response.""",
        )
        method: t.Optional[
            t.Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "CONNECT", "TRACE"]
        ] = Field(
            description="""When type is request, this is the HTTP method, otherwise it MUST be ignored. Its value 
            MUST be one of GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS, CONNECT, and TRACE.""",
        )
        query: t.Union[ReferenceObject, SchemaObject] = Field(
            description="""A Schema object containing the definitions for each query parameter. This schema MUST be of 
            type object and have a properties key.""",
        )

    class HTTPMessageBindingObject(_WithBindingVersion, _BaseModel):
        headers: t.Union[ReferenceObject, SchemaObject] = Field(
            description="""A Schema object containing the definitions for HTTP-specific headers. This schema MUST be 
            of type object and have a properties key.""",
        )


class AMQPBindingTrait:
    """
    This document defines how to describe AMQP-specific information on AsyncAPI.

    https://github.com/asyncapi/bindings/tree/master/amqp/README.md
    """

    class AMQPServerBindingObject(_BaseModel):
        """This object MUST NOT contain any properties. Its name is reserved for future use."""
        __root__: None

    class AMQPChannelBindingObject(_WithBindingVersion, _BaseModel):
        """
        This object contains information about the channel representation in AMQP.
        """

        class Config:
            schema_extra: t.ClassVar[t.Mapping[str, t.Any]] = {
                "examples": [
                    {
                        "is": "routingKey",
                        "queue": {
                            "name": "my-queue-name",
                            "durable": True,
                            "exclusive": True,
                            "autoDelete": False,
                            "vhost": "/",
                        },
                        "exchange": {
                            "name": "my-exchange",
                            "type": "topic",
                            "durable": True,
                            "autoDelete": False,
                            "vhost": "/",
                        },
                        "bindingVersion": "0.2.0",
                    },
                ],
            }

        class Exchange(_BaseModel):
            name: str = Field(
                max_length=255,
                description="""The name of the exchange. It MUST NOT exceed 255 characters long.""",
            )
            type_: t.Literal["topic", "direct", "fanout", "default", "headers"] = Field(
                alias="type",
                description="""The type of the exchange. Can be either topic, direct, fanout, default or headers.""",
            )
            durable: t.Optional[bool] = Field(
                description="""Whether the exchange should survive broker restarts or not.""",
            )
            auto_delete: t.Optional[bool] = Field(
                alias="autoDelete",
                description="""Whether the exchange should be deleted when the last queue is unbound from it.""",
            )
            vhost: str = Field(
                default="/",
                description="""The virtual host of the exchange. Defaults to /.""",
            )

        class Queue(_BaseModel):
            name: t.Optional[str] = Field(
                max_length=255,
                description="""The name of the queue. It MUST NOT exceed 255 characters long.""",
            )
            exclusive: t.Optional[bool] = Field(
                description="""Whether the queue should be used only by one connection or not.""",
            )
            durable: t.Optional[bool] = Field(
                description="""Whether the queue should survive broker restarts or not.""",
            )
            auto_delete: t.Optional[bool] = Field(
                alias="autoDelete",
                description="""Whether the queue should be deleted when the last consumer unsubscribes.""",
            )
            vhost: str = Field(
                default="/",
                description="""The virtual host of the queue. Defaults to /.""",
            )

        is_: t.Literal["queue", "routingKey"] = Field(
            default="routingKey",
            alias="is",
            description="""Defines what type of channel is it. Can be either queue or routingKey (default).""",
        )
        exchange: t.Optional[Exchange] = Field(
            description="""When is=routingKey, this object defines the exchange properties.""",
        )
        queue: t.Optional[Queue] = Field(
            description="""When is=queue, this object defines the queue properties.""",
        )

    class AMQPOperationBindingObject(_WithBindingVersion, _BaseModel):
        """This object contains information about the operation representation in AMQP."""

        class Config:
            schema_extra: t.ClassVar[t.Mapping[str, t.Any]] = {
                "examples": [
                    {
                        "expiration": 100000,
                        "userId": "guest",
                        "cc": ["user.logs"],
                        "priority": 10,
                        "deliveryMode": 2,
                        "mandatory": False,
                        "bcc": ["external.audit"],
                        "replyTo": "user.signedup",
                        "timestamp": True,
                        "ack": False,
                        "bindingVersion": "0.2.0",
                    },
                ],
            }

        expiration: t.Optional[int] = Field(
            ge=0,
            description="""Applies to: publish, subscribe; TTL (Time-To-Live) for the message. It MUST be greater 
            than or equal to zero.""",
        )
        user_id: t.Optional[str] = Field(
            alias="userId",
            description="""Applies to: publish, subscribe; Identifies the user who has sent the message.""",
        )
        cc: t.Optional[t.Sequence[str]] = Field(
            description="""Applies to: publish, subscribe; The routing keys the message should be routed to at the 
            time of publishing.""",
        )
        priority: t.Optional[int] = Field(
            description="""Applies to: publish, subscribe; A priority for the message.""",
        )
        delivery_mode: t.Optional[t.Literal[1, 2]] = Field(
            alias="deliveryMode",
            description="""Applies to: publish, subscribe; Delivery mode of the message. Its value MUST be either 1 (
            transient) or 2 (persistent).""",
        )
        mandatory: t.Optional[bool] = Field(
            description="""Applies to: publish; Whether the message is mandatory or not.""",
        )
        bcc: t.Optional[t.Sequence[str]] = Field(
            description="""Applies to: publish; Like cc but consumers will not receive this information.""",
        )
        reply_to: t.Optional[str] = Field(
            alias="replyTo",
            description="""Applies to: publish, subscribe; Name of the queue where the consumer should send the 
            response.""",
        )
        timestamp: t.Optional[bool] = Field(
            description="""Applies to: publish, subscribe; Whether the message should include a timestamp or not.""",
        )
        ack: t.Optional[bool] = Field(
            description="""Applies to: subscribe; Whether the consumer should ack the message or not.""",
        )

    class AMQPMessageBindingObject(_WithBindingVersion, _BaseModel):
        """This object contains information about the message representation in AMQP."""

        class Config:
            schema_extra: t.ClassVar[t.Mapping[str, t.Any]] = {
                "examples": [
                    {
                        "contentEncoding": "gzip",
                        "messageType": "user.signup",
                        "bindingVersion": "0.2.0",
                    },
                ],
            }

        content_encoding: t.Optional[str] = Field(
            alias="contentEncoding",
            description="""A MIME encoding for the message content.""",
        )
        message_type: t.Optional[str] = Field(
            alias="messageType",
            description="""Application-specific message type.""",
        )


class ExternalDocumentationObject(_WithDescriptionField, _WithSpecificationExtension, SpecObject, _BaseModel):
    url: AnyUrl = Field(
        description="""Required. The URL for the target documentation. Value MUST be in the format of a URL.""",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_external_documentation_object(self)


class _WithExternalDocsField(_BaseModel):
    external_docs: t.Optional[ExternalDocumentationObject] = Field(
        alias="externalDocs",
        description="""Additional external documentation for this tag.""",
    )


class TagObject(_WithDescriptionField, _WithExternalDocsField, _WithSpecificationExtension, SpecObject, _BaseModel):
    """
    Allows adding meta data to a single tag.

    https://www.asyncapi.com/docs/specifications/v2.2.0#tagObject
    """

    name: str = Field(
        description="""Required. The name of the tag.""",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_tag_object(self)


class TagsObject(SpecObject, _BaseModel):
    """
    A Tags object is a list of Tag Objects.

    https://www.asyncapi.com/docs/specifications/v2.2.0#tagsObject
    """

    __root__: t.Sequence[TagObject]

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_tags_object(self)


class _WithTagsField(_BaseModel):
    tags: t.Optional[TagsObject] = Field(
        description="""A list of tags for API documentation control. Tags can be used for logical grouping of 
        operations.""",
    )


class ContactObject(_WithSpecificationExtension, SpecObject, _BaseModel):
    """
    Contact information for the exposed API.

    https://www.asyncapi.com/docs/specifications/v2.2.0#contactObject
    """

    name: t.Optional[str] = Field(
        description="""The identifying name of the contact person/organization.""",
    )
    url: t.Optional[HttpUrl] = Field(
        description="""The URL pointing to the contact information. MUST be in the format of a URL.""",
    )
    email: t.Optional[Email] = Field(
        description="""The email address of the contact person/organization. MUST be in the format of an email 
        address.""",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_contact_object(self)


class LicenseObject(_WithSpecificationExtension, SpecObject, _BaseModel):
    """
    License information for the exposed API.

    https://www.asyncapi.com/docs/specifications/v2.2.0#licenseObject
    """

    name: str = Field(
        description="""Required. The license name used for the API.""",
    )
    url: t.Optional[HttpUrl] = Field(
        description="""A URL to the license used for the API. MUST be in the format of a URL.""",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_license_object(self)


class InfoObject(_WithDescriptionField, _WithSpecificationExtension, SpecObject, _BaseModel):
    """
    The object provides metadata about the API. The metadata can be used by the clients if needed.

    https://www.asyncapi.com/docs/specifications/v2.2.0#infoObject
    """

    title: str = Field(
        description="""Required. The title of the application.""",
    )
    version: str = Field(
        description="""Required. Provides the version of the application API (not to be confused with the 
        specification version).""",
    )
    terms_of_service: t.Optional[HttpUrl] = Field(
        alias="termsOfService",
        description="""A URL to the Terms of Service for the API. MUST be in the format of a URL.""",
    )
    contact: t.Optional[ContactObject] = Field(
        description="""The contact information for the exposed API.""",
    )
    license: t.Optional[LicenseObject] = Field(
        description="""The license information for the exposed API.""",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_info_object(self)


class ServerBindingsObject(_WithSpecificationExtension, SpecObject, _BaseModel):
    """
    Map describing protocol-specific definitions for a server.

    https://www.asyncapi.com/docs/specifications/v2.2.0#serverBindingsObject
    """

    # TODO: define fields for all supported protocols
    http: t.Optional[HTTPBindingTrait.HTTPServerBindingObject] = Field(
        description="""Protocol-specific information for an HTTP server.""",
    )
    amqp: t.Optional[AMQPBindingTrait.AMQPServerBindingObject] = Field(
        description="""Protocol-specific information for an AMQP 0-9-1 server.""",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_server_bindings_object(self)


class SecurityRequirementObject(SpecObject, _BaseModel):
    """
    Lists the required security schemes to execute this operation. The name used for each property MUST correspond to
    a security scheme declared in the Security Schemes under the Components Object. When a list of Security
    Requirement Objects is defined on a Server object, only one of the Security Requirement Objects in the list needs
    to be satisfied to authorize the connection.

    Each name MUST correspond to a security scheme which is declared in the Security Schemes under the Components
    Object. If the security scheme is of type "oauth2" or "openIdConnect", then the value is a list of scope names.
    Provide scopes that are required to establish successful connection with the server. If scopes are not needed,
    the list can be empty. For other security scheme types, the array MUST be empty.

    https://www.asyncapi.com/docs/specifications/v2.2.0#securityRequirementObject
    """

    __root__: t.Mapping[str, t.Sequence[str]]

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_security_requirement_object(self)


class ServerVariableObject(_WithSpecificationExtension, _WithDescriptionField, SpecObject, _BaseModel):
    """
    An object representing a Server Variable for server URL template substitution.

    https://www.asyncapi.com/docs/specifications/v2.2.0#serverVariableObject
    """

    enum: t.Optional[t.Sequence[str]] = Field(
        description="""An enumeration of string values to be used if the substitution options are from a limited 
        set.""",
    )
    default: t.Optional[str] = Field(
        description="""The default value to use for substitution, and to send, if an alternate value is not 
        supplied.""",
    )
    examples: t.Sequence[str] = Field(
        description="""An array of examples of the server variable.""",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_server_variable_object(self)


class ServerObject(_WithSpecificationExtension, _WithDescriptionField, SpecObject, _BaseModel):
    """
    An object representing a message broker, a server or any other kind of computer program capable of sending and/or
    receiving data. This object is used to capture details such as URIs, protocols and security configuration.
    Variable substitution can be used so that some details, for example usernames and passwords, can be injected by
    code generation tools.

    https://www.asyncapi.com/docs/specifications/v2.2.0#serverObject
    """
    url: AnyUrl = Field(
        description="""REQUIRED. A URL to the target host. This URL supports Server Variables and MAY be relative, 
        to indicate that the host location is relative to the location where the AsyncAPI document is being served. 
        Variable substitutions will be made when a variable is named in {brackets}.""",
    )
    protocol: t.Optional[Protocol] = Field(
        description="""The protocol this URL supports for connection.""",
    )
    protocol_version: t.Optional[str] = Field(
        alias="protocolVersion",
        description="""The version of the protocol used for connection. For instance: AMQP 0.9.1, HTTP 2.0, 
        Kafka 1.0.0, etc.""",
    )
    variables: t.Optional[t.Mapping[str, ServerVariableObject]] = Field(
        description="""A map between a variable name and its value. The value is used for substitution in the 
        server's URL template.""",
    )
    security: t.Optional[t.Sequence[SecurityRequirementObject]] = Field(
        description="""A declaration of which security mechanisms can be used with this server. The list of values 
        includes alternative security requirement objects that can be used. Only one of the security requirement 
        objects need to be satisfied to authorize a connection or operation. """,
    )
    bindings: t.Optional[t.Union[ReferenceObject, ServerBindingsObject]] = Field(
        description="""A map where the keys describe the name of the protocol and the values describe 
        protocol-specific definitions for the server.""",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_server_object(self)


class ServersObject(SpecObject, _BaseModel):
    """
    The Servers Object is a map of Server Objects.

    https://www.asyncapi.com/docs/specifications/v2.2.0#serversObject
    """

    __root__: t.Mapping[str, ServerObject]

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_servers_object(self)


class DefaultContentType(str, SpecObject):
    """
    A string representing the default content type to use when encoding/decoding a message's payload. The value MUST
    be a specific media type (e.g. application/json). This value MUST be used by schema parsers when the contentType
    property is omitted. In case a message can't be encoded/decoded using this value, schema parsers MUST use their
    default content type.

    https://www.asyncapi.com/docs/specifications/v2.2.0#defaultContentTypeString
    """

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_default_content_type(self)


class CorrelationIdObject(_WithDescriptionField, _WithSpecificationExtension, SpecObject, _BaseModel):
    """
    An object that specifies an identifier at design time that can used for message tracing and correlation. For
    specifying and computing the location of a Correlation ID, a runtime expression is used.

    https://www.asyncapi.com/docs/specifications/v2.2.0#correlationIdObject
    """

    location: RuntimeExpression = Field(
        description="""REQUIRED. A runtime expression that specifies the location of the correlation ID.""",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_correlation_id_object(self)


class MessageBindingsObject(_WithSpecificationExtension, SpecObject, _BaseModel):
    """
    Map describing protocol-specific definitions for a message.

    https://www.asyncapi.com/docs/specifications/v2.2.0#messageBindingsObject
    """
    http: t.Optional[HTTPBindingTrait.HTTPMessageBindingObject] = Field(
        description="""Protocol-specific information for an HTTP message, i.e., a request or a response.""",
    )
    amqp: t.Optional[AMQPBindingTrait.AMQPMessageBindingObject] = Field(
        description="""Protocol-specific information for an AMQP 0-9-1 message.""",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_message_bindings_object(self)


class MessageExampleObject(_WithSpecificationExtension, SpecObject, _BaseModel):
    """
    Message Example Object represents an example of a Message Object and MUST contain either headers and/or payload
    fields.

    https://www.asyncapi.com/docs/specifications/v2.2.0#messageExampleObject
    """
    headers: t.Optional[t.Mapping[str, t.Any]] = Field(
        description="""The value of this field MUST validate against the Message Object's headers field.""",
    )
    payload: t.Optional[t.Union[ReferenceObject, t.Any]] = Field(
        description="""The value of this field MUST validate against the Message Object's payload field.""",
    )
    name: t.Optional[str] = Field(
        description="""A machine-friendly name.""",
    )
    summary: t.Optional[str] = Field(
        description="""A short summary of what the example is about.""",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_message_example_object(self)


class MessageTraitObject(_WithDescriptionField, _WithTagsField, _WithExternalDocsField, SpecObject,
                         _WithSpecificationExtension,
                         _BaseModel):
    """
    Describes a trait that MAY be applied to a Message Object. This object MAY contain any property from the Message
    Object, except payload and traits. If you're looking to apply traits to an operation, see the Operation Trait
    Object.

    https://www.asyncapi.com/docs/specifications/v2.2.0#messageTraitObject
    """
    headers: t.Optional[t.Union[ReferenceObject, SchemaObject]] = Field(
        description="""Schema definition of the application headers. Schema MUST be of type "object". It MUST NOT 
        define the protocol headers.""",
    )
    correlation_id: t.Optional[t.Union[ReferenceObject, CorrelationIdObject]] = Field(
        alias="correlationId",
        description="""Definition of the correlation ID used for message tracing or matching.""",
    )
    schema_format: t.Optional[str] = Field(
        alias="schemaFormat",
        description="""A string containing the name of the schema format/language used to define the message payload. 
        If omitted, implementations should parse the payload as a Schema object.""",
    )
    content_type: t.Optional[str] = Field(
        alias="contentType",
        description="""The content type to use when encoding/decoding a message's payload. The value MUST be a 
        specific media type (e.g. application/json). When omitted, the value MUST be the one specified on the 
        defaultContentType field. """,
    )
    name: t.Optional[str] = Field(
        description="""A machine-friendly name for the message.""",
    )
    title: t.Optional[str] = Field(
        description="""A human-friendly title for the message.""",
    )
    summary: t.Optional[str] = Field(
        description="""A short summary of what the message is about.""",
    )
    bindings: t.Optional[t.Union[ReferenceObject, MessageBindingsObject]] = Field(
        description="""A map where the keys describe the name of the protocol and the values describe 
        protocol-specific definitions for the message. """,
    )
    examples: t.Optional[t.Sequence[MessageExampleObject]] = Field(
        description="""List of examples.""",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_message_trait_object(self)


class MessageObject(MessageTraitObject, SpecObject, _BaseModel):
    """
    Describes a message received on a given channel and operation.

    https://www.asyncapi.com/docs/specifications/v2.2.0#messageObject
    """
    payload: t.Union[ReferenceObject, SchemaObject]
    traits: t.Optional[t.Sequence[MessageTraitObject]]

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_message_object(self)


class OperationBindingsObject(_WithSpecificationExtension, SpecObject, _BaseModel):
    """
    Map describing protocol-specific definitions for an operation.

    https://www.asyncapi.com/docs/specifications/v2.2.0#operationBindingsObject
    """
    http: t.Optional[HTTPBindingTrait.HTTPOperationBindingObject] = Field(
        description="""Protocol-specific information for an HTTP operation.""",
    )
    amqp: t.Optional[AMQPBindingTrait.AMQPOperationBindingObject] = Field(
        description="""Protocol-specific information for an AMQP 0-9-1 operation.""",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_operation_bindings_object(self)


class OperationTraitObject(_WithDescriptionField, _WithTagsField, _WithExternalDocsField, SpecObject,
                           _WithSpecificationExtension,
                           _BaseModel):
    """
    Describes a trait that MAY be applied to an Operation Object. This object MAY contain any property from the
    Operation Object, except message and traits. If you're looking to apply traits to a message, see the Message
    Trait Object.

    https://www.asyncapi.com/docs/specifications/v2.2.0#operationTraitObject
    """

    operation_id: t.Optional[str] = Field(
        alias="operationId",
        description="""Unique string used to identify the operation. The id MUST be unique among all operations 
        described in the API. The operationId value is case-sensitive. Tools and libraries MAY use the operationId to 
        uniquely identify an operation, therefore, it is RECOMMENDED to follow common programming naming 
        conventions.""",
    )
    summary: t.Optional[str] = Field(
        description="""A short summary of what the operation is about.""",
    )
    bindings: t.Optional[t.Union[ReferenceObject, OperationBindingsObject]] = Field(
        description="""A map where the keys describe the name of the protocol and the values describe 
        protocol-specific definitions for the operation.""",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_operation_trait_object(self)


class OperationObject(OperationTraitObject, SpecObject, _BaseModel):
    """
    Describes a publish or a subscribe operation. This provides a place to document how and why messages are sent and
    received. For example, an operation might describe a chat application use case where a user sends a text message
    to a group. A publish operation describes messages that are received by the chat application, whereas a subscribe
    operation describes messages that are sent by the chat application.

    https://www.asyncapi.com/docs/specifications/v2.2.0#operationObject
    """

    traits: t.Optional[t.Sequence[t.Union[ReferenceObject, OperationTraitObject]]] = Field(
        description="""A list of traits to apply to the operation object. Traits MUST be merged into the operation 
        object using the JSON Merge Patch algorithm in the same order they are defined here.""",
    )
    message: t.Optional[t.Union[ReferenceObject, MessageObject, t.Sequence[t.Union[ReferenceObject, MessageObject]]]] \
        = Field(
        description="""A definition of the message that will be published or received on this channel. oneOf is 
        allowed here to specify multiple messages, however, a message MUST be valid only against one of the 
        referenced message objects.""",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_operation_object(self)


class ParameterObject(_WithDescriptionField, _WithSpecificationExtension, SpecObject, _BaseModel):
    """
    Describes a parameter included in a channel name.

    https://www.asyncapi.com/docs/specifications/v2.2.0#parameterObject
    """

    schema_: t.Optional[t.Union[ReferenceObject, SchemaObject]] = Field(
        alias="schema",
        description="""Definition of the parameter.""",
    )
    location: t.Optional[RuntimeExpression] = Field(
        description="""A runtime expression that specifies the location of the parameter value. Even when a 
        definition for the target field exists, it MUST NOT be used to validate this parameter but, instead, 
        the schema property MUST be used.""",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_parameter_object(self)


class ParametersObject(SpecObject, _BaseModel):
    """
    Describes a map of parameters included in a channel name. This map MUST contain all the parameters used in the
    parent channel name. The key represents the name of the parameter. It MUST match the parameter name used in the
    parent channel name.

    https://www.asyncapi.com/docs/specifications/v2.2.0#parametersObject
    """

    __root__: t.Mapping[ParameterName, t.Union[ReferenceObject, ParameterObject]]

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_parameters_object(self)


class ChannelBindingsObject(_WithSpecificationExtension, SpecObject, _BaseModel):
    """
    Map describing protocol-specific definitions for a channel.

    https://www.asyncapi.com/docs/specifications/v2.2.0#channelBindingsObject
    """

    # TODO: declare fields for all supported protocols
    http: t.Optional[HTTPBindingTrait.HTTPChannelBindingObject]
    amqp: t.Optional[AMQPBindingTrait.AMQPChannelBindingObject]

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_channel_bindings_object(self)


class ChannelItemObject(_WithDescriptionField, _WithSpecificationExtension, SpecObject, _BaseModel):
    """
    Describes the operations available on a single channel.

    https://www.asyncapi.com/docs/specifications/v2.2.0#channelItemObject
    """

    # TODO: check if `$ref` field should be defined here, or it just allowed to use `t.Union[ChannelItemObject,
    #  ReferenceObject]`
    servers: t.Optional[t.Sequence[str]] = Field(
        description="""The servers on which this channel is available, specified as an optional unordered list of 
        names (string keys) of Server Objects defined in the Servers Object (a map). If servers is absent or empty 
        then this channel must be available on all servers defined in the Servers Object. """,
    )
    subscribe: t.Optional[OperationObject] = Field(
        description="""A definition of the SUBSCRIBE operation, which defines the messages produced by the 
        application and sent to the channel.""",
    )
    publish: t.Optional[OperationObject] = Field(
        description="""A definition of the PUBLISH operation, which defines the messages consumed by the application 
        from the channel.""",
    )
    parameters: t.Optional[ParametersObject] = Field(
        description="""A map of the parameters included in the channel name. It SHOULD be present only when using 
        channels with expressions (as defined by RFC 6570 section 2.2).""",
    )
    bindings: t.Optional[t.Union[ReferenceObject, ChannelBindingsObject]] = Field(
        description="""A map where the keys describe the name of the protocol and the values describe 
        protocol-specific definitions for the channel.""",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_channel_item_object(self)


class ChannelsObject(SpecObject, _BaseModel):
    """
    Holds the relative paths to the individual channel and their operations. Channel paths are relative to servers.
    Channels are also known as "topics", "routing keys", "event types" or "paths".

    https://www.asyncapi.com/docs/specifications/v2.2.0#channelsObject
    """

    __root__: t.Mapping[str, t.Union[ReferenceObject, ChannelItemObject]]

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_channels_object(self)


class OAuthFlowObject(SpecObject, _BaseModel):
    """
    Configuration details for a supported OAuth Flow

    https://www.asyncapi.com/docs/specifications/v2.2.0#oauthFlowObject
    """

    # TODO: add applies to
    authorization_url: AnyUrl = Field(
        alias="authorizationUrl",
        description="""REQUIRED. The authorization URL to be used for this flow. This MUST be in the form of a URL.""",
    )
    token_url: AnyUrl = Field(
        alias="tokenUrl",
        description="""REQUIRED. The token URL to be used for this flow. This MUST be in the form of a URL.""",
    )
    refresh_url: t.Optional[AnyUrl] = Field(
        alias="refreshUrl",
        description="""The URL to be used for obtaining refresh tokens. This MUST be in the form of a URL.""",
    )
    scopes: t.Mapping[str, str] = Field(
        description="""REQUIRED. The available scopes for the OAuth2 security scheme. A map between the scope name 
        and a short description for it. """,
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_oauth_flow_object(self)


class OAuthFlowsObject(_WithSpecificationExtension, SpecObject, _BaseModel):
    """
    Allows configuration of the supported OAuth Flows.

    https://www.asyncapi.com/docs/specifications/v2.2.0#oauthFlowsObject
    """

    implicit: t.Optional[OAuthFlowObject] = Field(
        description="""Configuration for the OAuth Implicit flow""",
    )
    password: t.Optional[OAuthFlowObject] = Field(
        description="""Configuration for the OAuth Resource Owner Protected Credentials flow""",
    )
    client_credentials: t.Optional[OAuthFlowObject] = Field(
        alias="clientCredentials",
        description="""Configuration for the OAuth Client Credentials flow.""",
    )
    authorization_code: t.Optional[OAuthFlowObject] = Field(
        alias="authorizationCode",
        description="""Configuration for the OAuth Authorization Code flow.""",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_oauth_flows_object(self)


class SecuritySchemeObject(_WithDescriptionField, _WithSpecificationExtension, SpecObject, _BaseModel):
    """
    Defines a security scheme that can be used by the operations. Supported schemes are:
        * User/Password.
        * API key (either as user or as password).
        * X.509 certificate.
        * End-to-end encryption (either symmetric or asymmetric).
        * HTTP authentication.
        * HTTP API key.
        * OAuth2's common flows (Implicit, Resource Owner Protected Credentials, Client Credentials and Authorization
          Code) as defined in RFC6749.
        * OpenID Connect Discovery.
        * SASL (Simple Authentication and Security Layer) as defined in RFC4422.

    https://www.asyncapi.com/docs/specifications/v2.2.0#securitySchemeObject
    """
    # TODO: add applies to
    type_: SecuritySchemeType = Field(
        alias="type",
        description="""REQUIRED. The type of the security scheme. Valid values are "userPassword", "apiKey", "X509", 
        "symmetricEncryption", "asymmetricEncryption", "httpApiKey", "http", "oauth2", "openIdConnect", "plain", 
        "scramSha256", "scramSha512", and "gssapi".""",
    )
    name: t.Optional[str] = Field(
        description="""REQUIRED. The name of the header, query or cookie parameter to be used.""",
    )
    in_: t.Optional[str] = Field(
        alias="in",
        description="""REQUIRED. The location of the API key. Valid values are "user" and "password" for apiKey and 
        "query", "header" or "cookie" for httpApiKey. """,
    )
    scheme: t.Optional[str] = Field(
        description="""REQUIRED. The name of the HTTP Authorization scheme to be used in the Authorization header as 
        defined in RFC7235. """,
    )
    bearer_format: t.Optional[str] = Field(
        alias="bearerFormat",
        description="""A hint to the client to identify how the bearer token is formatted. Bearer tokens are usually 
        generated by an authorization server, so this information is primarily for documentation purposes. """,
    )
    flows: t.Optional[OAuthFlowsObject] = Field(
        description="""REQUIRED. An object containing configuration information for the flow types supported.""",
    )
    open_id_connect_url: t.Optional[AnyUrl] = Field(
        alias="openIdConnectUrl",
        description="""REQUIRED. OpenId Connect URL to discover OAuth2 configuration values. This MUST be in the form 
        of a URL.""",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_security_scheme_object(self)


class ComponentsObject(_WithSpecificationExtension, SpecObject, _BaseModel):
    """
    Holds a set of reusable objects for different aspects of the AsyncAPI specification. All objects defined within
    the components object will have no effect on the API unless they are explicitly referenced from properties
    outside the components object.

    https://www.asyncapi.com/docs/specifications/v2.2.0#componentsObject
    """
    schemas: t.Optional[t.Mapping[str, t.Union[ReferenceObject, SchemaObject]]] = Field(
        description="""An object to hold reusable Schema Objects.""",
    )
    messages: t.Optional[t.Mapping[str, t.Union[ReferenceObject, MessageObject]]] = Field(
        description="""An object to hold reusable Message Objects.""",
    )
    security_schemes: t.Optional[t.Mapping[str, t.Union[ReferenceObject, SecuritySchemeObject]]] = Field(
        alias="securitySchemes",
        description="""An object to hold reusable Security Scheme Objects.""",
    )
    parameters: t.Optional[t.Mapping[str, t.Union[ReferenceObject, ParameterObject]]] = Field(
        description="""An object to hold reusable Parameter Objects.""",
    )
    correlation_ids: t.Optional[t.Mapping[str, t.Union[ReferenceObject, CorrelationIdObject]]] = Field(
        alias="correlationIds",
        description="""An object to hold reusable Correlation ID Objects.""",
    )
    operation_traits: t.Optional[t.Mapping[str, t.Union[ReferenceObject, OperationTraitObject]]] = Field(
        alias="operationTraits",
        description="""An object to hold reusable Operation Trait Objects.""",
    )
    message_traits: t.Optional[t.Mapping[str, t.Union[ReferenceObject, MessageTraitObject]]] = Field(
        alias="messageTraits",
        description="""An object to hold reusable Message Trait Objects.""",
    )
    server_bindings: t.Optional[t.Mapping[str, t.Union[ReferenceObject, ServerBindingsObject]]] = Field(
        alias="serverBindings",
        description="""An object to hold reusable Server Bindings Objects.""",
    )
    channel_bindings: t.Optional[t.Mapping[str, t.Union[ReferenceObject, ChannelBindingsObject]]] = Field(
        alias="channelBindings",
        description="""An object to hold reusable Channel Bindings Objects.""",
    )
    operation_bindings: t.Optional[t.Mapping[str, t.Union[ReferenceObject, OperationBindingsObject]]] = Field(
        alias="operationBindings",
        description="""An object to hold reusable Operation Bindings Objects.""",
    )
    message_bindings: t.Optional[t.Mapping[str, t.Union[ReferenceObject, MessageBindingsObject]]] = Field(
        alias="messageBindings",
        description="""An object to hold reusable Message Bindings Objects.""",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_components_object(self)


class AsyncAPIObject(_WithTagsField, _WithExternalDocsField, _WithSpecificationExtension, SpecObject, _BaseModel):
    """
    This is the root document object for the API specification. It combines resource listing and API declaration
    together into one document.

    https://www.asyncapi.com/docs/specifications/v2.2.0#A2SObject
    """

    asyncapi: SemanticVersion = Field(
        description="""Required. Specifies the AsyncAPI Specification version being used. It can be used by tooling 
        Specifications and clients to interpret the version. The structure shall be major.minor.patch, where patch 
        versions must be compatible with the existing major.minor tooling. Typically patch versions will be 
        introduced to address errors in the documentation, and tooling should typically be compatible with the 
        corresponding major.minor (1.0.*). Patch versions will correspond to patches of this document.""",
    )
    id: t.Optional[Identifier] = Field(
        description="""Identifier of the application the AsyncAPI document is defining.""",
    )
    info: InfoObject = Field(
        description="""Required. Provides metadata about the API. The metadata can be used by the clients if needed.""",
    )
    servers: t.Optional[ServersObject] = Field(
        description="""Provides connection details of servers.""",
    )
    default_content_type: t.Optional[DefaultContentType] = Field(
        alias="defaultContentType",
        description="""Default content type to use when encoding/decoding a message's payload.""",
    )
    channels: ChannelsObject = Field(
        description="""Required The available channels and messages for the API.""",
    )
    components: t.Optional[ComponentsObject] = Field(
        description="""An element to hold various schemas for the specification.""",
    )

    def accept_visitor(self, visitor: "SpecObjectVisitor[T]") -> T:
        return visitor.visit_async_api_object(self)

    def iter_channels(self) -> t.Iterable[t.Tuple[str, ChannelItemObject]]:
        for _, channels in self.channels:
            for channel_name, channel in channels.items():
                yield channel_name, channel

    def iter_channel_publish_operations(self) -> t.Iterable[t.Tuple[str, ChannelItemObject, OperationObject]]:
        for channel_name, channel in self.iter_channels():
            if operation := as_(OperationObject, channel.publish):
                yield channel_name, channel, operation

    def iter_channel_subscribe_operations(self) -> t.Iterable[t.Tuple[str, ChannelItemObject, OperationObject]]:
        for channel_name, channel in self.iter_channels():
            if operation := as_(OperationObject, channel.subscribe):
                yield channel_name, channel, operation

    def iter_channel_operations(self) -> t.Iterable[t.Tuple[str, ChannelItemObject, OperationObject]]:
        for channel_name, channel in self.iter_channels():
            if operation := as_(OperationObject, channel.publish):
                yield channel_name, channel, operation

            if operation := as_(OperationObject, channel.subscribe):
                yield channel_name, channel, operation


# TODO: add string type and visit it
class SpecObjectVisitor(t.Generic[T_co], metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def visit_identifier(self, obj: Identifier) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_runtime_expression(self, obj: RuntimeExpression) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_reference_object(self, obj: ReferenceObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_schema_object(self, obj: SchemaObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_external_documentation_object(self, obj: ExternalDocumentationObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_tag_object(self, obj: TagObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_tags_object(self, obj: TagsObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_contact_object(self, obj: ContactObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_license_object(self, obj: LicenseObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_info_object(self, obj: InfoObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_server_bindings_object(self, obj: ServerBindingsObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_security_requirement_object(self, obj: SecurityRequirementObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_server_variable_object(self, obj: ServerVariableObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_server_object(self, obj: ServerObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_servers_object(self, obj: ServersObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_default_content_type(self, obj: DefaultContentType) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_correlation_id_object(self, obj: CorrelationIdObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_message_bindings_object(self, obj: MessageBindingsObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_message_example_object(self, obj: MessageExampleObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_message_trait_object(self, obj: MessageTraitObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_message_object(self, obj: MessageObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_operation_bindings_object(self, obj: OperationBindingsObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_operation_trait_object(self, obj: OperationTraitObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_operation_object(self, obj: OperationObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_parameter_object(self, obj: ParameterObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_parameters_object(self, obj: ParametersObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_channel_bindings_object(self, obj: ChannelBindingsObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_channel_item_object(self, obj: ChannelItemObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_channels_object(self, obj: ChannelsObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_oauth_flow_object(self, obj: OAuthFlowObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_oauth_flows_object(self, obj: OAuthFlowsObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_security_scheme_object(self, obj: SecuritySchemeObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_components_object(self, obj: ComponentsObject) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_async_api_object(self, obj: AsyncAPIObject) -> T_co:
        raise NotImplementedError
