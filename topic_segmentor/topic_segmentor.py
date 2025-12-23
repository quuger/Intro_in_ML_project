from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ChatMessage:
    user: str
    text: str
    timestamp: int  # unix seconds


Topic = List[ChatMessage]


class TopicSegmentor(ABC):
    @abstractmethod
    def get_topics(self, path: str) -> List[Topic]:
        raise NotImplementedError

    @staticmethod
    def load_messages(path: str) -> List[ChatMessage]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        messages: List[ChatMessage] = []
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                continue
            username = item.get("user")
            content = item.get("text")
            timestamp = item.get("timestamp")

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

            messages.append(ChatMessage(user=username, text=content.strip(), timestamp=ts))

        messages.sort(key=lambda m: m.timestamp)
        return messages