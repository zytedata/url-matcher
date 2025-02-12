from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast


def load_json_fixture(name: str) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], json.loads((Path(__file__).parent / "fixtures" / f"{name}.json").read_text()))
