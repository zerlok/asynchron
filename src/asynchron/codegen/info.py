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
    enable_meta_doc: bool = True
    ignore_formatter: bool = True
    use_absolute_imports: bool = True
