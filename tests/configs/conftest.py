from pathlib import Path

from pytest_cases import fixture


@fixture()
def target_dir(tmp_path: Path) -> Path:
    return tmp_path


@fixture()
def project_name() -> str:
    return "testproject"
