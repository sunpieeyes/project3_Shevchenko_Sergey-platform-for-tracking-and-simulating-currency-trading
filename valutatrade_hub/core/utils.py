# Здесь будут функции для работы с JSON, валидации и т.д.

def load_json(path: str):
    import json
    try:
        with open(path, "r", encoding="utf8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def save_json(path: str, data):
    import json
    with open(path, "w", encoding="utf8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
