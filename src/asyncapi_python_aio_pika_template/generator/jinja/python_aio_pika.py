__all__ = (
    "JinjaBasedPythonAioPikaCodeGenerator",
)

import typing as t
from pathlib import Path

from jinja2 import Template

from asyncapi_python_aio_pika_template.app import AsyncApiCodeGenerator
from asyncapi_python_aio_pika_template.spec import AsyncAPIObject

# TODO: write correct templates
TEMPLATE = """
{% for name, channel in config.channels %}
    {{ channel }}
{% endfor %}
"""


class JinjaBasedPythonAioPikaCodeGenerator(AsyncApiCodeGenerator):

    def generate(self, config: AsyncAPIObject) -> t.Iterable[t.Tuple[Path, t.TextIO]]:
        yield Path("main.py"), Template(TEMPLATE).render(config=config)
