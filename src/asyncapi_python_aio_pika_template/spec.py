import abc
import re
import typing as t

from pydantic import AnyUrl, BaseModel, Extra, Field, HttpUrl

T = t.TypeVar("T")


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


class ServerName(StringRegexValidator, pattern=re.compile(r"^[A-Za-z0-9_\-]+$")):
    pass


class Protocol(BaseModel):
    """
    The supported protocol.
    """
    __root__: t.Literal["amqp", "amqps", "http", "https", "ibmmq", "jms", "kafka", "kafka-secure", "anypointmq", "mqtt",
                        "secure-mqtt", "stomp", "stomps", "ws", "wss", "mercure"]


class Traits:
    class Field:
        DESCRIPTION: t.Final[t.Any] = Field(
            description="""A short description of the application. <a href="https://spec.commonmark.org/">CommonMark 
            syntax</a> can be used for rich text representation.""",
        )


class SpecificationExtension(BaseModel):
    """
    https://www.asyncapi.com/docs/specifications/v2.2.0#specificationExtensions
    """

    # TODO: add validator
    class Config:
        extra = Extra.allow


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


class ContactObject(SpecificationExtension, BaseModel):
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


class LicenseObject(SpecificationExtension, BaseModel):
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


class InfoObject(SpecificationExtension, BaseModel):
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
    description: t.Optional[str] = Traits.Field.DESCRIPTION
    termsOfService: t.Optional[HttpUrl] = Field(
        description="""A URL to the Terms of Service for the API. MUST be in the format of a URL.""",
    )
    contact: t.Optional[ContactObject] = Field(
        description="""The contact information for the exposed API.""",
    )
    license: t.Optional[LicenseObject] = Field(
        description="""The license information for the exposed API.""",
    )


class SchemaObject(BaseModel):
    """
    The Schema Object allows the definition of input and output data types. These types can be objects,
    but also primitives and arrays. This object is a superset of the JSON Schema Specification Draft 07. The empty
    schema (which allows any instance to validate) MAY be represented by the boolean value true and a schema which
    allows no instance to validate MAY be represented by the boolean value false. Further information about the
    properties can be found in JSON Schema Core and JSON Schema Validation. Unless stated otherwise, the property
    definitions follow the JSON Schema specification as referenced here.
    """

    # TODO: make a correct type (look at properties)
    # FIXME: TypeError: Object of type '_GenericAlias' is not JSON serializable
    # __root__ = t.Union[bool, int, float, str, t.Sequence[t.Any], t.Mapping[str, t.Any]]
    __root__ = bool


class HTTPServerBinding(BaseModel):
    """
    This document defines how to describe HTTP-specific information on AsyncAPI.

    https://github.com/asyncapi/bindings/tree/master/http#server
    """
    type_: t.Literal["request", "response"] = Field(
        title="type",
        description="""Required. Type of operation. Its value MUST be either request or response.""",
    )
    method: t.Optional[t.Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "CONNECT", "TRACE"]] = \
        Field(
            description="""When type is request, this is the HTTP method, otherwise it MUST be ignored. Its value 
            MUST be one of GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS, CONNECT, and TRACE.""",
        )
    query: SchemaObject = Field(
        description="""A Schema object containing the definitions for each query parameter. This schema MUST be of 
        type object and have a properties key.""",
    )
    bindingVersion: t.Optional[str] = Field(
        description="""The version of this binding. If omitted, "latest" MUST be assumed.""",
    )


class WebSocketsServerBinding(BaseModel):
    # TODO: define fields
    pass


class AMQPServerBinding(BaseModel):
    # TODO: define fields
    pass


class ServerBindingsObject(SpecificationExtension, BaseModel):
    """
    Map describing protocol-specific definitions for a server.

    https://www.asyncapi.com/docs/specifications/v2.2.0#serverBindingsObject
    """
    # TODO: define all fields
    http: HTTPServerBinding = Field(
        description="""Protocol-specific information for an HTTP server.""",
    )
    ws: WebSocketsServerBinding = Field(
        description="""Protocol-specific information for a WebSockets server.""",
    )
    amqp: AMQPServerBinding = Field(
        description="""Protocol-specific information for an AMQP 0-9-1 server.""",
    )


class ServerVariableObject(SpecificationExtension, BaseModel):
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
    description: t.Optional[str] = Traits.Field.DESCRIPTION
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


class ServerObject(SpecificationExtension, BaseModel):
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
    description: t.Optional[str] = Traits.Field.DESCRIPTION
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


class AsyncAPIObject(SpecificationExtension, BaseModel):
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

    id: Identifier = Field(
        description="""Identifier of the application the AsyncAPI document is defining.""",
    )
    info: InfoObject = Field(
        description="""Required. Provides metadata about the API. The metadata can be used by the clients if needed.""",
    )
    servers: t.Mapping[ServerName, ServerObject] = Field(
        description="""Provides connection details of servers.""",
    )
    defaultContentType: t.Any = Field(
        description="""Default content type to use when encoding/decoding a message's payload.""",
    )
    channels: t.Any = Field(
        description="""Required The available channels and messages for the API.""",
    )
    components: t.Any = Field(
        description="""An element to hold various schemas for the specification.""",
    )
    tags: t.Any = Field(
        description="""A list of tags used by the specification with additional metadata. Each tag name in the list 
        MUST be unique.""",
    )
    externalDocs: t.Any = Field(
        description="""Additional external documentation.""",
    )


if __name__ == "__main__":
    import json

    print(json.dumps(AsyncAPIObject.schema(), indent=2))
