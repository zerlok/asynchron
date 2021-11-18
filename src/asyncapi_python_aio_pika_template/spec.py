import abc
import re
import typing as t
from pathlib import Path
from pprint import pprint

import yaml
from pydantic import AnyUrl, BaseModel, Field, HttpUrl

T = t.TypeVar("T")
# FIXME:  NameError: Field name "schema" shadows a BaseModel attribute; use a different field name with "alias='schema'".

class Validator(metaclass=abc.ABCMeta):

    @classmethod
    def __get_validators__(cls: t.Type[T]) -> t.Iterable[t.Callable[[t.Any], T]]:
        yield cls.validate

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
        if not isinstance(value, str):
            raise TypeError("Unexpected type", value)

        if not cls._PATTERN.match(value):
            raise ValueError(f"Invalid {cls.__name__} value", value)

        return cls(value)


class Email(StringRegexValidator, pattern=re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")):
    """
    An email string.

    https://emailregex.com/
    """
    pass


class SemanticVersion(StringRegexValidator):
    """
    A valid semantic version type.

    https://semver.org

    Regex was taken from https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
    """

    _PATTERN: t.ClassVar[t.Pattern[str]] = re.compile(
        r"^"
        r"(?P<major>0|[1-9]\d*)"
        r"\.(?P<minor>0|[1-9]\d*)"
        r"\.(?P<patch>0|[1-9]\d*)"
        r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
        r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
        r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"
        r"$""")


class Identifier(StringRegexValidator):
    """
    This field represents a unique universal identifier of the application the AsyncAPI document is defining. It must
    conform to the URI format, according to RFC3986. It is RECOMMENDED to use a URN to globally and uniquely identify
    the application during long periods of time, even after it becomes unavailable or ceases to exist.

    https://www.asyncapi.com/docs/specifications/v2.2.0#A2SIdString
    """

    _PATTERN: t.ClassVar[t.Pattern[str]] = re.compile(r"^urn:[a-z0-9][a-z0-9-]{0,31}:[a-z0-9()+,\-.:=@;$_!*'%/?#]+$")


class RuntimeExpression(str):
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
    pass


class ServerName(StringRegexValidator, pattern=re.compile(r"^[A-Za-z0-9_\-]+$")):
    pass


class ParameterName(StringRegexValidator, pattern=re.compile(r"^[A-Za-z0-9_\-]+$")):
    pass


class ComponentName(StringRegexValidator, pattern=re.compile(r"^[a-zA-Z0-9\.\-_]+$")):
    pass


class Protocol(BaseModel):
    """
    The supported protocol.
    """
    __root__: t.Literal["amqp", "amqps", "http", "https", "ibmmq", "jms", "kafka", "kafka-secure", "anypointmq", "mqtt",
                        "secure-mqtt", "stomp", "stomps", "ws", "wss", "mercure"]


class SecuritySchemeType(BaseModel):
    """
    The supported security scheme type.
    """

    __root__: t.Literal["userPassword", "apiKey", "X509", "symmetricEncryption", "asymmetricEncryption", "httpApiKey",
                        "http", "oauth2", "openIdConnect", "plain", "scramSha256", "scramSha512", "gssapi"]


class ReferenceObject(BaseModel):
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

    ref: AnyUrl = Field(
        alias="$ref",
        description="""Required. The reference string.""",
    )


class SchemaObject(BaseModel):
    """
    The Schema Object allows the definition of input and output data types. These types can be objects,
    but also primitives and arrays. This object is a superset of the JSON Schema Specification Draft 07. The empty
    schema (which allows any instance to validate) MAY be represented by the boolean value true and a schema which
    allows no instance to validate MAY be represented by the boolean value false. Further information about the
    properties can be found in JSON Schema Core and JSON Schema Validation. Unless stated otherwise, the property
    definitions follow the JSON Schema specification as referenced here.

    https://www.asyncapi.com/docs/specifications/v2.2.0#schemaObject
    """

    __root__: t.Mapping[str, t.Any]

    # TODO: read and define fields according to json schema spec
    #  http://json-schema.org/draft/2020-12/json-schema-core.html
    """
    title: t.Optional[str]
    type: t.Optional[str]
    required: t.Optional[str]
    multipleOf: t.Optional[str]
    maximum: t.Optional[str]
    exclusiveMaximum: t.Optional[str]
    minimum: t.Optional[str]
    exclusiveMinimum: t.Optional[str]
    maxLength: t.Optional[str]
    minLength: t.Optional[str]
    pattern: t.Optional[str] = Field(
        description="This string SHOULD be a valid regular expression, according to the ECMA 262 regular expression "
                    "dialect.",
    )
    maxItems: t.Optional[str]
    minItems: t.Optional[str]
    uniqueItems: t.Optional[str]
    maxProperties: t.Optional[str]
    minProperties: t.Optional[str]
    enum: t.Optional[str]
    const: t.Optional[str]
    examples: t.Optional[str]
    if_: t.Optional[str]
    then: t.Optional[str]
    else_: t.Optional[str]
    readOnly: t.Optional[str]
    writeOnly: t.Optional[str]
    properties: t.Optional[str]
    patternProperties: t.Optional[str]
    additionalProperties: t.Optional[str]
    additionalItems: t.Optional[str]
    items: t.Optional[str]
    propertyNames: t.Optional[str]
    contains: t.Optional[str]
    allOf: t.Optional[str]
    oneOf: t.Optional[str]
    anyOf: t.Optional[str]
    not_: t.Optional[str]
    """


class WithBindingVersion(BaseModel):
    bindingVersion: t.Optional[str] = Field(
        description="""The version of this binding. If omitted, "latest" MUST be assumed.""",
    )


class HTTPBindingTrait:
    """
    https://github.com/asyncapi/bindings/blob/master/http/README.md
    """

    class HTTPServerBindingObject(BaseModel):
        """This object MUST NOT contain any properties. Its name is reserved for future use."""
        __root__: None

    class HTTPChannelBindingObject(BaseModel):
        """This object MUST NOT contain any properties. Its name is reserved for future use."""
        __root__: None

    class HTTPOperationBindingObject(WithBindingVersion, BaseModel):
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
        query: t.Union[SchemaObject, ReferenceObject] = Field(
            description="""A Schema object containing the definitions for each query parameter. This schema MUST be of 
            type object and have a properties key.""",
        )

    class HTTPMessageBindingObject(WithBindingVersion, BaseModel):
        headers: t.Union[SchemaObject, ReferenceObject] = Field(
            description="""A Schema object containing the definitions for HTTP-specific headers. This schema MUST be 
            of type object and have a properties key.""",
        )


class AMQPBindingTrait:
    """
    This document defines how to describe AMQP-specific information on AsyncAPI.

    https://github.com/asyncapi/bindings/tree/master/amqp/README.md
    """

    class AMQPServerBindingObject(BaseModel):
        """This object MUST NOT contain any properties. Its name is reserved for future use."""
        __root__: None

    class AMQPChannelBindingObject(WithBindingVersion, BaseModel):
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

        class Exchange(BaseModel):
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
            autoDelete: t.Optional[bool] = Field(
                description="""Whether the exchange should be deleted when the last queue is unbound from it.""",
            )
            vhost: str = Field(
                default="/",
                description="""The virtual host of the exchange. Defaults to /.""",
            )

        class Queue(BaseModel):
            name: str = Field(
                max_length=255,
                description="""The name of the queue. It MUST NOT exceed 255 characters long.""",
            )
            exclusive: t.Optional[bool] = Field(
                description="""Whether the queue should be used only by one connection or not.""",
            )
            durable: t.Optional[bool] = Field(
                description="""Whether the queue should survive broker restarts or not.""",
            )
            autoDelete: t.Optional[bool] = Field(
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
        queue: t.Optional[Exchange] = Field(
            description="""When is=queue, this object defines the queue properties.""",
        )

    class AMQPOperationBindingObject(WithBindingVersion, BaseModel):
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
        userId: t.Optional[str] = Field(
            description="""Applies to: publish, subscribe; Identifies the user who has sent the message.""",
        )
        cc: t.Optional[t.Sequence[str]] = Field(
            description="""Applies to: publish, subscribe; The routing keys the message should be routed to at the 
            time of publishing.""",
        )
        priority: t.Optional[int] = Field(
            description="""Applies to: publish, subscribe; A priority for the message.""",
        )
        deliveryMode: t.Optional[t.Literal[1, 2]] = Field(
            description="""Applies to: publish, subscribe; Delivery mode of the message. Its value MUST be either 1 (
            transient) or 2 (persistent).""",
        )
        mandatory: t.Optional[bool] = Field(
            description="""Applies to: publish; Whether the message is mandatory or not.""",
        )
        bcc: t.Optional[t.Sequence[str]] = Field(
            description="""Applies to: publish; Like cc but consumers will not receive this information.""",
        )
        replyTo: t.Optional[str] = Field(
            description="""Applies to: publish, subscribe; Name of the queue where the consumer should send the 
            response.""",
        )
        timestamp: t.Optional[bool] = Field(
            description="""Applies to: publish, subscribe; Whether the message should include a timestamp or not.""",
        )
        ack: t.Optional[bool] = Field(
            description="""Applies to: subscribe; Whether the consumer should ack the message or not.""",
        )

    class AMQPMessageBindingObject(WithBindingVersion, BaseModel):
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

        contentEncoding: t.Optional[str] = Field(
            description="""A MIME encoding for the message content.""",
        )
        messageType: t.Optional[str] = Field(
            description="""Application-specific message type.""",
        )


class WithDescriptionField(BaseModel):
    description: t.Optional[str] = Field(
        description="""A short description of the application. <a href="https://spec.commonmark.org/">CommonMark 
        syntax</a> can be used for rich text representation.""",
    )


class ExternalDocumentationObject(WithDescriptionField, BaseModel):
    url: AnyUrl = Field(
        description="""Required. The URL for the target documentation. Value MUST be in the format of a URL.""",
    )


class WithExternalDocsField(BaseModel):
    externalDocs: t.Optional[ExternalDocumentationObject] = Field(
        description="""Additional external documentation for this tag.""",
    )


class TagObject(WithDescriptionField, WithExternalDocsField, BaseModel):
    """
    Allows adding meta data to a single tag.

    https://www.asyncapi.com/docs/specifications/v2.2.0#tagObject
    """
    name: str = Field(
        description="""Required. The name of the tag.""",
    )


class TagsObject(BaseModel):
    """
    A Tags object is a list of Tag Objects.

    https://www.asyncapi.com/docs/specifications/v2.2.0#tagsObject
    """

    __root__: t.Sequence[TagObject]


class WithTagsField(BaseModel):
    tags: t.Optional[TagsObject] = Field(
        description="""A list of tags for API documentation control. Tags can be used for logical grouping of 
        operations.""",
    )


class WithSpecificationExtension(BaseModel):
    """
    https://www.asyncapi.com/docs/specifications/v2.2.0#specificationExtensions
    """

    # TODO: add validator
    # class Config:
    #     extra = Extra.allow


class ContactObject(WithSpecificationExtension, BaseModel):
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


class LicenseObject(WithSpecificationExtension, BaseModel):
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


class InfoObject(WithSpecificationExtension, WithDescriptionField, BaseModel):
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
    termsOfService: t.Optional[HttpUrl] = Field(
        description="""A URL to the Terms of Service for the API. MUST be in the format of a URL.""",
    )
    contact: t.Optional[ContactObject] = Field(
        description="""The contact information for the exposed API.""",
    )
    license: t.Optional[LicenseObject] = Field(
        description="""The license information for the exposed API.""",
    )


class ServerBindingsObject(WithSpecificationExtension, BaseModel):
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


class ServerVariableObject(WithSpecificationExtension, WithDescriptionField, BaseModel):
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


class SecurityRequirementObject(BaseModel):
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


class ServerObject(WithSpecificationExtension, WithDescriptionField, BaseModel):
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
    protocol: Protocol = Field(
        description="""The protocol this URL supports for connection.""",
    )
    protocolVersion: t.Optional[str] = Field(
        description="""The version of the protocol used for connection. For instance: AMQP 0.9.1, HTTP 2.0, 
        Kafka 1.0.0, etc.""",
    )
    variables: t.Optional[t.Mapping[str, ServerVariableObject]] = Field(
        description="""A map between a variable name and its value. The value is used for substitution in the 
        server's URL template.""",
    )
    security: t.Sequence[SecurityRequirementObject] = Field(
        description="""A declaration of which security mechanisms can be used with this server. The list of values 
        includes alternative security requirement objects that can be used. Only one of the security requirement 
        objects need to be satisfied to authorize a connection or operation. """,
    )
    bindings: t.Union[ServerBindingsObject, ReferenceObject] = Field(
        description="""A map where the keys describe the name of the protocol and the values describe 
        protocol-specific definitions for the server.""",
    )


class ServersObject(BaseModel):
    """
    The Servers Object is a map of Server Objects.

    https://www.asyncapi.com/docs/specifications/v2.2.0#serversObject
    """

    __root__: t.Mapping[ServerName, ServerObject]


class DefaultContentType(str):
    """
    A string representing the default content type to use when encoding/decoding a message's payload. The value MUST
    be a specific media type (e.g. application/json). This value MUST be used by schema parsers when the contentType
    property is omitted. In case a message can't be encoded/decoded using this value, schema parsers MUST use their
    default content type.

    https://www.asyncapi.com/docs/specifications/v2.2.0#defaultContentTypeString
    """
    pass


class CorrelationIdObject(WithDescriptionField, WithSpecificationExtension, BaseModel):
    """
    An object that specifies an identifier at design time that can used for message tracing and correlation. For
    specifying and computing the location of a Correlation ID, a runtime expression is used.

    https://www.asyncapi.com/docs/specifications/v2.2.0#correlationIdObject
    """

    location: RuntimeExpression = Field(
        description="""REQUIRED. A runtime expression that specifies the location of the correlation ID.""",
    )


class MessageBindingsObject(WithSpecificationExtension, BaseModel):
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


class MessageExampleObject(WithSpecificationExtension, BaseModel):
    """
    Message Example Object represents an example of a Message Object and MUST contain either headers and/or payload
    fields.

    https://www.asyncapi.com/docs/specifications/v2.2.0#messageExampleObject
    """
    headers: t.Optional[t.Mapping[str, t.Any]] = Field(
        description="""The value of this field MUST validate against the Message Object's headers field.""",
    )
    payload: t.Optional[t.Any] = Field(
        description="""The value of this field MUST validate against the Message Object's payload field.""",
    )
    name: t.Optional[str] = Field(
        description="""A machine-friendly name.""",
    )
    summary: t.Optional[str] = Field(
        description="""A short summary of what the example is about.""",
    )


class MessageTraitObject(WithDescriptionField, WithTagsField, WithExternalDocsField, WithSpecificationExtension,
                         BaseModel):
    """
    Describes a trait that MAY be applied to a Message Object. This object MAY contain any property from the Message
    Object, except payload and traits. If you're looking to apply traits to an operation, see the Operation Trait
    Object.

    https://www.asyncapi.com/docs/specifications/v2.2.0#messageTraitObject
    """
    headers: t.Optional[t.Union[SchemaObject, ReferenceObject]] = Field(
        description="""Schema definition of the application headers. Schema MUST be of type "object". It MUST NOT 
        define the protocol headers.""",
    )
    correlationId: t.Optional[t.Union[CorrelationIdObject, ReferenceObject]] = Field(
        description="""Definition of the correlation ID used for message tracing or matching.""",
    )
    schemaFormat: t.Optional[str] = Field(
        description="""A string containing the name of the schema format/language used to define the message payload. 
        If omitted, implementations should parse the payload as a Schema object.""",
    )
    contentType: t.Optional[str] = Field(
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
    bindings: t.Optional[t.Union[MessageBindingsObject, ReferenceObject]] = Field(
        description="""A map where the keys describe the name of the protocol and the values describe 
        protocol-specific definitions for the message. """,
    )
    examples: t.Optional[t.Sequence[MessageExampleObject]] = Field(
        description="""List of examples.""",
    )


class MessageObject(MessageTraitObject, BaseModel):
    """
    Describes a message received on a given channel and operation.

    https://www.asyncapi.com/docs/specifications/v2.2.0#messageObject
    """
    payload: t.Any
    traits: t.Optional[t.Sequence[MessageTraitObject]]


class OperationBindingsObject(WithSpecificationExtension, BaseModel):
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


class OperationTraitObject(WithDescriptionField, WithTagsField, WithExternalDocsField, BaseModel):
    """
    Describes a trait that MAY be applied to an Operation Object. This object MAY contain any property from the
    Operation Object, except message and traits. If you're looking to apply traits to a message, see the Message
    Trait Object.

    https://www.asyncapi.com/docs/specifications/v2.2.0#operationTraitObject
    """

    operationId: t.Optional[str] = Field(
        description="""Unique string used to identify the operation. The id MUST be unique among all operations 
        described in the API. The operationId value is case-sensitive. Tools and libraries MAY use the operationId to 
        uniquely identify an operation, therefore, it is RECOMMENDED to follow common programming naming 
        conventions.""",
    )
    summary: t.Optional[str] = Field(
        description="""A short summary of what the operation is about.""",
    )
    bindings: t.Optional[t.Union[OperationBindingsObject, ReferenceObject]] = Field(
        description="""A map where the keys describe the name of the protocol and the values describe 
        protocol-specific definitions for the operation.""",
    )


class OperationObject(OperationTraitObject, WithSpecificationExtension, BaseModel):
    """
    Describes a publish or a subscribe operation. This provides a place to document how and why messages are sent and
    received. For example, an operation might describe a chat application use case where a user sends a text message
    to a group. A publish operation describes messages that are received by the chat application, whereas a subscribe
    operation describes messages that are sent by the chat application.

    https://www.asyncapi.com/docs/specifications/v2.2.0#operationObject
    """

    traits: t.Optional[t.Sequence[t.Union[OperationTraitObject, ReferenceObject]]] = Field(
        description="""A list of traits to apply to the operation object. Traits MUST be merged into the operation 
        object using the JSON Merge Patch algorithm in the same order they are defined here.""",
    )
    message: t.Optional[t.Sequence[t.Union[MessageObject, ReferenceObject]]] = Field(
        description="""A definition of the message that will be published or received on this channel. oneOf is 
        allowed here to specify multiple messages, however, a message MUST be valid only against one of the 
        referenced message objects.""",
    )


class ParameterObject(WithDescriptionField, WithSpecificationExtension, BaseModel):
    """
    Describes a parameter included in a channel name.

    https://www.asyncapi.com/docs/specifications/v2.2.0#parameterObject
    """

    schema: t.Optional[t.Union[SchemaObject, ReferenceObject]] = Field(
        description="""Definition of the parameter.""",
    )
    location: t.Optional[RuntimeExpression] = Field(
        description="""A runtime expression that specifies the location of the parameter value. Even when a 
        definition for the target field exists, it MUST NOT be used to validate this parameter but, instead, 
        the schema property MUST be used.""",
    )


class ParametersObject(BaseModel):
    """
    Describes a map of parameters included in a channel name. This map MUST contain all the parameters used in the
    parent channel name. The key represents the name of the parameter. It MUST match the parameter name used in the
    parent channel name.

    https://www.asyncapi.com/docs/specifications/v2.2.0#parametersObject
    """

    __root__: t.Mapping[ParameterName, t.Union[ParameterObject, ReferenceObject]]


class ChannelBindingsObject(BaseModel):
    """
    Map describing protocol-specific definitions for a channel.

    https://www.asyncapi.com/docs/specifications/v2.2.0#channelBindingsObject
    """

    # TODO: declare fields for all supported protocols
    http: t.Optional[HTTPBindingTrait.HTTPChannelBindingObject]
    amqp: t.Optional[AMQPBindingTrait.AMQPChannelBindingObject]


class ChannelItemObject(WithDescriptionField, WithSpecificationExtension, BaseModel):
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
    bindings: t.Optional[t.Union[ChannelBindingsObject, ReferenceObject]] = Field(
        description="""A map where the keys describe the name of the protocol and the values describe 
        protocol-specific definitions for the channel.""",
    )


class ChannelsObject(BaseModel):
    """
    Holds the relative paths to the individual channel and their operations. Channel paths are relative to servers.
    Channels are also known as "topics", "routing keys", "event types" or "paths".

    https://www.asyncapi.com/docs/specifications/v2.2.0#channelsObject
    """

    __root__: t.Mapping[str, t.Union[ChannelItemObject, ReferenceObject]]


class OAuthFlowObject(BaseModel):
    """
    Configuration details for a supported OAuth Flow

    https://www.asyncapi.com/docs/specifications/v2.2.0#oauthFlowObject
    """

    # TODO: add applies to
    authorizationUrl: AnyUrl = Field(
        description="""REQUIRED. The authorization URL to be used for this flow. This MUST be in the form of a URL.""",
    )
    tokenUrl: AnyUrl = Field(
        description="""REQUIRED. The token URL to be used for this flow. This MUST be in the form of a URL.""",
    )
    refreshUrl: t.Optional[AnyUrl] = Field(
        description="""The URL to be used for obtaining refresh tokens. This MUST be in the form of a URL.""",
    )
    scopes: t.Mapping[str, str] = Field(
        description="""REQUIRED. The available scopes for the OAuth2 security scheme. A map between the scope name 
        and a short description for it. """,
    )


class OAuthFlowsObject(WithSpecificationExtension, BaseModel):
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
    clientCredentials: t.Optional[OAuthFlowObject] = Field(
        description="""Configuration for the OAuth Client Credentials flow.""",
    )
    authorizationCode: t.Optional[OAuthFlowObject] = Field(
        description="""Configuration for the OAuth Authorization Code flow.""",
    )


class SecuritySchemeObject(WithDescriptionField, WithSpecificationExtension, BaseModel):
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
    name: str = Field(
        description="""REQUIRED. The name of the header, query or cookie parameter to be used.""",
    )
    in_: str = Field(
        alias="in",
        description="""REQUIRED. The location of the API key. Valid values are "user" and "password" for apiKey and 
        "query", "header" or "cookie" for httpApiKey. """,
    )
    scheme: str = Field(
        description="""REQUIRED. The name of the HTTP Authorization scheme to be used in the Authorization header as 
        defined in RFC7235. """,
    )
    bearerFormat: t.Optional[str] = Field(
        description="""A hint to the client to identify how the bearer token is formatted. Bearer tokens are usually 
        generated by an authorization server, so this information is primarily for documentation purposes. """,
    )
    flows: OAuthFlowsObject = Field(
        description="""REQUIRED. An object containing configuration information for the flow types supported.""",
    )
    openIdConnectUrl: str = Field(
        description="""REQUIRED. OpenId Connect URL to discover OAuth2 configuration values. This MUST be in the form 
        of a URL.""",
    )


class ComponentsObject:
    """
    Holds a set of reusable objects for different aspects of the AsyncAPI specification. All objects defined within
    the components object will have no effect on the API unless they are explicitly referenced from properties
    outside the components object.

    https://www.asyncapi.com/docs/specifications/v2.2.0#componentsObject
    """
    schemas: t.Optional[t.Mapping[str, t.Union[SchemaObject, ReferenceObject]]] = Field(
        description="""An object to hold reusable Schema Objects.""",
    )
    messages: t.Optional[t.Mapping[str, t.Union[MessageObject, ReferenceObject]]] = Field(
        description="""An object to hold reusable Message Objects.""",
    )
    securitySchemes: t.Optional[t.Mapping[str, t.Union[SecuritySchemeObject, ReferenceObject]]] = Field(
        description="""An object to hold reusable Security Scheme Objects.""",
    )
    parameters: t.Optional[t.Mapping[str, t.Union[ParameterObject, ReferenceObject]]] = Field(
        description="""An object to hold reusable Parameter Objects.""",
    )
    correlationIds: t.Optional[t.Mapping[str, t.Union[CorrelationIdObject, ReferenceObject]]] = Field(
        description="""An object to hold reusable Correlation ID Objects.""",
    )
    operationTraits: t.Optional[t.Mapping[str, t.Union[OperationTraitObject, ReferenceObject]]] = Field(
        description="""An object to hold reusable Operation Trait Objects.""",
    )
    messageTraits: t.Optional[t.Mapping[str, t.Union[MessageTraitObject, ReferenceObject]]] = Field(
        description="""An object to hold reusable Message Trait Objects.""",
    )
    serverBindings: t.Optional[t.Mapping[str, t.Union[ServerBindingsObject, ReferenceObject]]] = Field(
        description="""An object to hold reusable Server Bindings Objects.""",
    )
    channelBindings: t.Optional[t.Mapping[str, t.Union[ChannelBindingsObject, ReferenceObject]]] = Field(
        description="""An object to hold reusable Channel Bindings Objects.""",
    )
    operationBindings: t.Optional[t.Mapping[str, t.Union[OperationBindingsObject, ReferenceObject]]] = Field(
        description="""An object to hold reusable Operation Bindings Objects.""",
    )
    messageBindings: t.Optional[t.Mapping[str, t.Union[MessageBindingsObject, ReferenceObject]]] = Field(
        description="""An object to hold reusable Message Bindings Objects.""",
    )


class AsyncAPIObject(WithTagsField, WithExternalDocsField, WithSpecificationExtension, BaseModel):
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
    defaultContentType: t.Optional[DefaultContentType] = Field(
        description="""Default content type to use when encoding/decoding a message's payload.""",
    )
    channels: ChannelsObject = Field(
        description="""Required The available channels and messages for the API.""",
    )
    components: ComponentsObject = Field(
        description="""An element to hold various schemas for the specification.""",
    )


if __name__ == "__main__":

    # print(json.dumps(AsyncAPIObject.schema(), indent=2))
    with (Path(__file__).parent.parent / "temperature.yaml").open("r") as fd:
        spec = AsyncAPIObject.parse_obj(yaml.safe_load(fd))

    pprint(spec.dict())
