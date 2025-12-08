import json
import os
from tempfile import NamedTemporaryFile
import shutil


def read_json(path: str):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return None


def write_json_atomic(path: str, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
        json.dump(data, tmp, indent=4, ensure_ascii=False)
        temp_name = tmp.name

    shutil.move(temp_name, path)
