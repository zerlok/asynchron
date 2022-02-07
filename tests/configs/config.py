import functools as ft
import json
import typing as t
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

from pytest_cases import lazy_value, parametrize

F = t.TypeVar("F", bound=t.Callable[..., t.Any])


@dataclass(frozen=True)
class CodegenConfig:
    path: Path

    asyncapi_config_path: Path
    normalized_config_json_path: Path
    normalized_config: object

    generated_code_dir: Path
    generated_code_file_content: t.Mapping[Path, str]


def iter_dir_by_relative_paths(root: Path) -> t.Iterable[t.Tuple[Path, Path]]:
    abs_root = root.absolute()
    root_parts_len = len(abs_root.parts)

    for inner in abs_root.iterdir():
        yield inner, Path(*inner.parts[root_parts_len:])


def load_file_content(path: Path) -> str:
    with path.open("r") as fd:
        return fd.read()


def load_codegen_config_from_dir(
        config_dir: Path,
        asyncapi_yaml: str,
        normalized_asyncapi_json: str,
        generated_code_dir: str,
) -> CodegenConfig:
    normalized_asyncapi_json_path = config_dir / normalized_asyncapi_json

    with normalized_asyncapi_json_path.open("r") as fd:
        normalized_config = json.load(fd)

    generated_code_dir_path = config_dir / generated_code_dir

    return CodegenConfig(
        path=config_dir,
        asyncapi_config_path=config_dir / asyncapi_yaml,
        normalized_config_json_path=normalized_asyncapi_json_path,
        normalized_config=normalized_config,
        generated_code_dir=generated_code_dir_path,
        generated_code_file_content=OrderedDict(sorted(
            (
                (rel_path, load_file_content(path))
                for path, rel_path in iter_dir_by_relative_paths(generated_code_dir_path)
                if path.is_file()
            ),
            key=lambda x: x[0],
        )),
    )


def use_codegen_config_from_dir_as_fixture(
        config_dir: Path,
        id_: t.Optional[str] = None,
        arg_name: str = "config",
        asyncapi_yaml: str = "asyncapi.yaml",
        normalized_asyncapi_json: str = "final.json",
        generated_code_dir: str = "generated",
) -> t.Callable[[F], F]:
    assert config_dir.is_dir()

    def wrapper(func: F) -> F:
        parametrizer = parametrize(
            argnames=(arg_name,),
            argvalues=(
                lazy_value(ft.partial(load_codegen_config_from_dir, config_dir, asyncapi_yaml, normalized_asyncapi_json,
                                      generated_code_dir, )),
            ),
            ids=(
                id_ if id_ is not None else func.__name__,
            ),
        )

        return parametrizer(func)

    return wrapper
