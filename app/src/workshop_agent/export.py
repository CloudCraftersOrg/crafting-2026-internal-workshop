"""export.py – Investigation bundle serialisation helpers."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class _Turn:
    role: str
    content: str
    correlation_id: Optional[str]
    ts: str


@dataclass
class Bundle:
    session_id: str
    model_id: str
    aws_region: str
    turns: list[_Turn]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "model_id": self.model_id,
            "aws_region": self.aws_region,
            "created_at": self.created_at,
            "turns": [
                {
                    "role": t.role,
                    "content": t.content,
                    "correlation_id": t.correlation_id,
                    "ts": t.ts,
                }
                for t in self.turns
            ],
        }


class BundleBuilder:
    def __init__(self, session_id: str, model_id: str, aws_region: str) -> None:
        self._session_id = session_id
        self._model_id = model_id
        self._aws_region = aws_region
        self._turns: list[_Turn] = []
        self._created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def add_turn(
        self,
        role: str,
        content: str,
        correlation_id: Optional[str] = None,
    ) -> None:
        self._turns.append(
            _Turn(
                role=role,
                content=content,
                correlation_id=correlation_id,
                ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
        )

    def build(self) -> Bundle:
        return Bundle(
            session_id=self._session_id,
            model_id=self._model_id,
            aws_region=self._aws_region,
            turns=list(self._turns),
            created_at=self._created_at,
        )


def export_bundle(
    bundle: Bundle,
    output_dir: str = "./exports",
    logger: Any = None,
) -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    filename = f"bundle_{bundle.session_id}.json"
    path = os.path.join(output_dir, filename)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(bundle.to_dict(), fh, indent=2, ensure_ascii=False)
    if logger is not None:
        logger.info("bundle_exported", path=path, session_id=bundle.session_id)
    return path
