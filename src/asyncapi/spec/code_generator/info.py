__all__ = (
    "AsyncApiCodeGeneratorMetaInfo",
)

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class AsyncApiCodeGeneratorMetaInfo:
    generator_name: str
    generator_link: str
    generator_started_at: datetime
    config_path: Path
    project_name: str
    author: str
