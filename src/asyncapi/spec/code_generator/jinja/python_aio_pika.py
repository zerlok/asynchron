__all__ = (
    "JinjaBasedPythonAioPikaCodeGenerator",
)

import typing as t
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from asyncapi.app import AsyncApiCodeGenerator
from asyncapi.spec.base import AsyncAPIObject, SchemaObject

K = t.TypeVar("K", bound=t.Hashable)
V = t.TypeVar("V")
T = t.TypeVar("T")


def _map(*values: t.Optional[T]) -> t.Iterable[T]:
    for value in values:
        if value is not None:
            yield value


@dataclass(frozen=True)
class MessageFieldDef:
    name: str
    description: t.Optional[str]
    type: str
    alias: str


@dataclass(frozen=True)
class MessageDef:
    name: str
    description: t.Optional[str]
    fields: t.Mapping[str, MessageFieldDef]


@dataclass(frozen=True)
class ConsumerDef:
    name: str
    description: t.Optional[str]
    message: MessageDef
    exchange_name: str
    queue_name: t.Optional[str]
    binding_keys: t.Collection[str]


@dataclass(frozen=True)
class ManagerDef:
    name: str
    description: t.Optional[str]


@dataclass(frozen=True)
class ModuleDef:
    name: str
    description: t.Optional[str]
    python_path: str


@dataclass(frozen=True)
class AppDef:
    name: str
    description: t.Optional[str]
    modules: t.Mapping[str, ModuleDef]
    consumers: t.Mapping[str, ConsumerDef]
    manager: ManagerDef


class JinjaBasedPythonAioPikaCodeGenerator(AsyncApiCodeGenerator):

    def __init__(self) -> None:
        self.__jinja_env = Environment(
            loader=FileSystemLoader(Path(__file__).parent / "templates"),
        )
        self.__jinja_env.filters.update({
            "to_snake_case": self.__make_snake_case,
            "to_pascal_case": self.__make_pascal_case,
            "ordered_values": self.__iter_ordered_values,
            # "iter_message_payloads": self.__iter_message_payloads,
        })

    def generate(self, config: AsyncAPIObject) -> t.Iterable[t.Tuple[Path, t.Iterable[str]]]:
        modules = [
            ModuleDef(
                name="__main__",
                python_path="app.__main__",
                description=None,
            ),
            ModuleDef(
                name="message",
                python_path="app.message",
                description=None,
            ),
            ModuleDef(
                name="consumer",
                python_path="app.consumer",
                description=None,
            ),
        ]

        kwargs = {
            "app": AppDef(
                name=config.info.title,
                description=config.info.description,
                modules=self.__build_mapping_by_name(*modules),
                consumers=self.__build_mapping_by_name(*self.__iter_consumers(config)),
                manager=ManagerDef(
                    name=config.info.title,
                    description=config.info.description,
                ),
            ),
        }

        for module in modules:
            yield Path(f"{module.name}.py"), self.__jinja_env.get_template(f"{module.name}.jinja2").stream(**kwargs)

    def __make_snake_case(self, value: str) -> str:
        # FIXME: implement a correct method
        return value.replace(" ", "_").lower()

    def __make_pascal_case(self, value: str) -> str:
        # FIXME: implement a correct method
        return "".join(v.capitalize() for v in value.replace(" ", "_").replace("-", "_").split("_"))

    def __iter_ordered_values(self, value: t.Mapping[K, V]) -> t.Iterable[V]:
        return (v for _, v in sorted(value.items(), key=lambda pair: pair[0]))

    def __build_mapping_by_name(self, *objs: V) -> t.Mapping[str, V]:
        return {
            obj.name: obj
            for obj in objs
        }

    def __iter_consumers(self, config: AsyncAPIObject) -> t.Iterable[MessageDef]:
        for _, channels in config.channels:
            for channel_name, channel in channels.items():
                channel_alias = channel_name.replace("/", "_")
                for operation in _map(channel.publish):
                    for message in _map(operation.message):
                        payload = message.payload
                        if isinstance(payload, SchemaObject):
                            yield ConsumerDef(
                                name=channel_alias,
                                description="...",
                                message=MessageDef(
                                    name="_".join((channel_alias, payload.__root__["title"])),
                                    description=payload.__root__.get("description"),
                                    fields={
                                        prop_name: MessageFieldDef(
                                            name=prop_name,
                                            description=prop.get("description"),
                                            type=prop,
                                            alias=prop.get("alias", prop_name),
                                        )
                                        for prop_name, prop in payload.__root__["properties"].items()
                                    },
                                ),
                                exchange_name=channel.bindings.amqp.exchange.name,
                                queue_name=channel.bindings.amqp.queue.name,
                                binding_keys=operation.bindings.amqp.cc,
                            )

    def __get_first_by_key(self, values: t.Iterable[T], key_getter: t.Callable[[T], K]) -> t.Mapping[K, T]:
        groups: t.Dict[K, T] = {}

        for value in values:
            key = key_getter(value)
            groups.setdefault(key, value)

        return groups
