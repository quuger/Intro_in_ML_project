import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional


@dataclass
class Message:
    id: int
    user: str
    text: str
    timestamp: int
    reply_to_id: Optional[int] = None


def _extract_text(msg: Dict[str, Any]) -> str:
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


def _extract_reply_to_id(msg: Dict[str, Any]) -> Optional[int]:
    """
    Telegram export variants:
      - reply_to_message_id: int
      - reply_to: {"message_id": int, ...}   (sometimes)
    We'll support both.
    """
    r1 = msg.get("reply_to_message_id")
    if r1 is not None:
        try:
            return int(r1)
        except (TypeError, ValueError):
            return None

    r2 = msg.get("reply_to")
    if isinstance(r2, dict):
        mid = r2.get("message_id")
        if mid is not None:
            try:
                return int(mid)
            except (TypeError, ValueError):
                return None

    return None


def parse_telegram_export(path: str) -> List[Message]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    user_map: Dict[str, str] = {}
    next_user_id = 1
    result: List[Message] = []

    for msg in data.get("messages", []):
        if msg.get("type") != "message":
            continue

        msg_id = msg.get("id")
        raw_user = msg.get("from")
        timestamp = msg.get("date_unixtime")

        if msg_id is None or not raw_user or timestamp is None:
            continue

        try:
            msg_id_int = int(msg_id)
        except (TypeError, ValueError):
            continue

        text = _extract_text(msg)
        if not text:
            continue

        if raw_user not in user_map:
            user_map[raw_user] = f"user{next_user_id}"
            next_user_id += 1

        reply_to_id = _extract_reply_to_id(msg)

        result.append(
            Message(
                id=msg_id_int,
                user=user_map[raw_user],
                text=text,
                timestamp=int(timestamp),
                reply_to_id=reply_to_id,
            )
        )

    return result


def preprocess_telegram_data(path: str, save_path="raw_data/messages.json"):
    messages = parse_telegram_export(path)

    with open(save_path, "w+", encoding="utf-8") as f:
        json.dump([asdict(m) for m in messages], f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    path_to_telegram_data = input("Enter path to telegram data: ")
    preprocess_telegram_data(path_to_telegram_data)
    print(parse_telegram_export(path_to_telegram_data))
