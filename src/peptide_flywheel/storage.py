from __future__ import annotations

from pathlib import Path
from typing import Type, TypeVar
import json
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def save_json_record(record: BaseModel, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(record.model_dump_json(indent=2), encoding="utf-8")


def load_json_record(model_cls: Type[T], path: str | Path) -> T:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return model_cls.model_validate(data)


def append_jsonl(record: BaseModel, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(record.model_dump_json() + "\n")
