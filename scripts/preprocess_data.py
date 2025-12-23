import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any


@dataclass
class Message:
    user: str
    text: str
    timestamp: int


def _extract_text(msg: Dict[str, Any]) -> str:
    """
    Telegram export:
    - msg["text"] can be "" | str | list[{"type": "...", "text": "..."}]
    - msg["text_entities"] can be [] | list[{"type": "...", "text": "..."}]
    We prefer text_entities (as requested) and join all .text parts into one string.
    """
    source = msg.get("text_entities")
    if isinstance(source, list) and source:
        parts = []
        for item in source:
            if isinstance(item, dict):
                t = item.get("text")
                if isinstance(t, str) and t:
                    parts.append(t)
            elif isinstance(item, str) and item:
                parts.append(item)
        return "".join(parts).strip()

    text = msg.get("text", "")
    if isinstance(text, str):
        return text.strip()

    if isinstance(text, list):
        parts = []
        for item in text:
            if isinstance(item, dict):
                t = item.get("text")
                if isinstance(t, str) and t:
                    parts.append(t)
            elif isinstance(item, str) and item:
                parts.append(item)
        return "".join(parts).strip()

    return ""


def parse_telegram_export(path: str) -> List[Message]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    user_map: Dict[str, str] = {}
    next_user_id = 1
    result: List[Message] = []

    for msg in data.get("messages", []):
        if msg.get("type") != "message":
            continue

        raw_user = msg.get("from")
        timestamp = msg.get("date_unixtime")

        if not raw_user or timestamp is None:
            continue

        text = _extract_text(msg)
        if not text:
            continue

        if raw_user not in user_map:
            user_map[raw_user] = f"user{next_user_id}"
            next_user_id += 1

        result.append(
            Message(
                user=user_map[raw_user],
                text=text,
                timestamp=int(timestamp),
            )
        )

    return result

def preprocess_telegram_data(path: str, save_path="raw_data/messages.json"):
    messages = parse_telegram_export(path)

    with open(save_path, "w+", encoding="utf-8") as f:
        json.dump(
            [asdict(m) for m in messages],
            f,
            ensure_ascii=False,
            indent=2
        )

if __name__ == '__main__':
    path_to_telegram_data = input("Enter path to telegram data: ")
    preprocess_telegram_data(path_to_telegram_data)
    print(parse_telegram_export(path_to_telegram_data))
