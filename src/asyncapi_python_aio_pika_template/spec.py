import abc
import re
import typing as t
from pydantic import BaseModel, EmailStr, Field, HttpUrl

T = t.TypeVar("T")


class TypeValidator(metaclass=abc.ABCMeta):

    @classmethod
    def __get_validators__(cls: t.Type[T]) -> t.Iterable[t.Callable[[t.Any], T]]:
        yield cls.validate

    @classmethod
    @abc.abstractmethod
    def validate(cls: t.Type[T], value: t.Any) -> T:
        raise NotImplementedError


class SemanticVersion(str, TypeValidator):
    """
    A valid semantic version type.

    Regex was taken from https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
    """

    __PATTERN: t.Final[t.Pattern[str]] = re.compile(
        r"^"
        r"(?P<major>0|[1-9]\d*)"
        r"\.(?P<minor>0|[1-9]\d*)"
        r"\.(?P<patch>0|[1-9]\d*)"
        r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
        r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
        r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"
        r"$""")

    @classmethod
    def validate(cls, value: t.Any) -> "SemanticVersion":
        if not isinstance(value, str):
            raise TypeError("Unexpected type", value)

        if not cls.__PATTERN.match(value):
            raise ValueError("Invalid semver value", value)

        return cls(value)


class URN(str, TypeValidator):
    __PATTERN: t.Final[t.Pattern[str]] = re.compile(r"^urn:[a-z0-9][a-z0-9-]{0,31}:[a-z0-9()+,\-.:=@;$_!*'%/?#]+$")

    @classmethod
    def validate(cls, value: t.Any) -> "URN":
        if not isinstance(value, str):
            raise TypeError("Unexpected type", value)

        if not cls.__PATTERN.match(value):
            raise ValueError("Invalid semver value", value)

        return cls(value)


class Contact(BaseModel):
    name: t.Optional[str] = Field(
        description="""The identifying name of the contact person/organization.""",
    )
    url: t.Optional[HttpUrl] = Field(
        description="""The URL pointing to the contact information. MUST be in the format of a URL.""",
    )
    email: t.Optional[EmailStr] = Field(
        description="""The email address of the contact person/organization. MUST be in the format of an email 
        address.""",
    )


class License(BaseModel):
    name: str = Field(
        description="""Required. The license name used for the API.""",
    )
    url: t.Optional[HttpUrl] = Field(
        description="""A URL to the license used for the API. MUST be in the format of a URL.""",
    )


class Info(BaseModel):
    title: str = Field(
        description="""Required. The title of the application.""",
    )
    version: str = Field(
        description="""Required Provides the version of the application API (not to be confused with the 
        specification version).""",
    )
    description: t.Optional[str] = Field(
        description="""A short description of the application. <a href="https://spec.commonmark.org/">CommonMark 
        syntax</a> can be used for rich text representation.""",
    )
    termsOfService: t.Optional[HttpUrl] = Field(
        description="""A URL to the Terms of Service for the API. MUST be in the format of a URL.""",
    )
    contact: t.Optional[Contact] = Field(
        description="""The contact information for the exposed API.""",
    )
    license: t.Optional[License] = Field(
        description="""The license information for the exposed API.""",
    )


class AsyncAPI(BaseModel):

    asyncapi: SemanticVersion = Field(
        description="""Required. Specifies the AsyncAPI Specification version being used. It can be used by tooling 
        Specifications and clients to interpret the version. The structure shall be major.minor.patch, where patch 
        versions must be compatible with the existing major.minor tooling. Typically patch versions will be 
        introduced to address errors in the documentation, and tooling should typically be compatible with the 
        corresponding major.minor (1.0.*). Patch versions will correspond to patches of this document.""",
    )

    id: URN = Field(
        description="""Identifier of the application the AsyncAPI document is defining.""",
    )
    info: Info = Field(
        description="""Required. Provides metadata about the API. The metadata can be used by the clients if needed.""",
    )
    servers: t.Any
    defaultContentType: t.Any
    channels: t.Any
    components: t.Any
    tags: t.Any
    externalDocs: t.Any

"""
asyncapi	AsyncAPI Version String	Required. Specifies the AsyncAPI Specification version being used. It can be used by tooling Specifications and clients to interpret the version. The structure shall be major.minor.patch, where patch versions must be compatible with the existing major.minor tooling. Typically patch versions will be introduced to address errors in the documentation, and tooling should typically be compatible with the corresponding major.minor (1.0.*). Patch versions will correspond to patches of this document.
id	Identifier	Identifier of the application the AsyncAPI document is defining.
info	Info Object	Required. Provides metadata about the API. The metadata can be used by the clients if needed.
servers	Servers Object	Provides connection details of servers.
defaultContentType	Default Content Type	Default content type to use when encoding/decoding a message's payload.
channels	Channels Object	Required The available channels and messages for the API.
components	Components Object	An element to hold various schemas for the specification.
tags	Tags Object	A list of tags used by the specification with additional metadata. Each tag name in the list MUST be unique.
externalDocs	External Documentation Object	Additional external documentation.
"""
