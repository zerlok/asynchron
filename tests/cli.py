import typing as t
from dataclasses import dataclass, field

from click.testing import Result

from asynchron.codegen.cli import CLIContainer


@dataclass(frozen=True)
class CliInput:
    obj: t.Optional[CLIContainer] = None
    args: t.Sequence[str] = field(default_factory=tuple)
    env: t.Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CliOutput:
    exit_code: int = 0
    stdout: str = ""


CliRunner = t.Callable[[CliInput], Result]
