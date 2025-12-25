from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ChatMessage:
    id: int
    user: str
    text: str
    timestamp: int  # unix seconds
    reply_to_id: Optional[int] = None


Topic = List[ChatMessage]


class TopicSegmentor(ABC):
    __topic_size: int = 4

    def __init__(self, topic_size: int):
        if topic_size < 1:
            raise ValueError("topic_size must be at least 1")
        self.__topic_size = topic_size

    def get_topic_size(self) -> int:
        return self.__topic_size

    @abstractmethod
    def get_topics(self, path: str) -> List[Topic]:
        raise NotImplementedError

    @staticmethod
    def load_messages(path: str) -> List[ChatMessage]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        messages: List[ChatMessage] = []
        for item in data:
            if not isinstance(item, dict):
                continue

            msg_id = item.get("id")
            username = item.get("user")
            content = item.get("text")
            timestamp = item.get("timestamp")
            reply_to_id = item.get("reply_to_id", None)

            try:
                msg_id_int = int(msg_id)
            except (TypeError, ValueError):
                continue

            if not isinstance(username, str) or not username:
                continue
            if not isinstance(content, str) or not content.strip():
                continue
            if timestamp is None:
                continue

            try:
                ts = int(timestamp)
            except (TypeError, ValueError):
                continue

            rpl: Optional[int] = None
            if reply_to_id is not None:
                try:
                    rpl = int(reply_to_id)
                except (TypeError, ValueError):
                    rpl = None

            messages.append(
                ChatMessage(
                    id=msg_id_int,
                    user=username,
                    text=content.strip(),
                    timestamp=ts,
                    reply_to_id=rpl,
                )
            )

        messages.sort(key=lambda m: m.timestamp)
        return messages
