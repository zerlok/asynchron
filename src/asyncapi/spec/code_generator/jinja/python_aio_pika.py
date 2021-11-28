__all__ = (
    "JinjaBasedPythonAioPikaCodeGenerator",
)

import typing as t
from pathlib import Path

from jinja2 import Template

from asyncapi.app import AsyncApiCodeGenerator
from asyncapi.spec.base import AsyncAPIObject

T = t.TypeVar("T")


def _map(*values: t.Optional[T]) -> t.Iterable[T]:
    for value in values:
        if value is not None:
            yield value


class JinjaBasedPythonAioPikaCodeGenerator(AsyncApiCodeGenerator):

    def __init__(self) -> None:
        with (Path(__file__).parent / "templates" / "gen.jinja2").open("r") as fd:
            self.__template = Template(fd.read())

    def generate(self, config: AsyncAPIObject) -> t.Iterable[t.Tuple[Path, t.Iterable[str]]]:
        yield Path("message.py"), self.__template.stream(context={
            "messages": [
                {
                    "name": message.name,
                    "payload": message.payload.__root__ if message.payload is not None and not isinstance(
                        message.payload, bool) else None,
                }
                for _, channels in config.channels
                for name, channel in channels.items()
                for sub in _map(channel.subscribe, channel.publish)
                for message in _map(sub.message)
            ]
        })
