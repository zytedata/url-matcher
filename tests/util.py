import json
from pathlib import Path


def load_json_fixture(name):
    return json.loads((Path(__file__).parent / "fixtures" / f"{name}.json").read_text())
