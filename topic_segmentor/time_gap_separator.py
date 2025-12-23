from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .topic_segmentor import TopicSegmentor, Topic, ChatMessage


@dataclass
class TimeGapTopicSegmentor(TopicSegmentor):
    """
    Heuristic:
    Consecutive messages belong to the same topic
    if the time difference between them is <= max_gap_seconds.
    """
    max_gap_seconds: int = 120

    def get_topics(self, path: str) -> List[Topic]:
        messages = self.load_messages(path)
        if not messages:
            return []

        topics: List[Topic] = []
        current: Topic = [messages[0]]

        for msg in messages[1:]:
            prev: ChatMessage = current[-1]
            if msg.timestamp - prev.timestamp <= self.max_gap_seconds:
                current.append(msg)
            else:
                topics.append(current)
                current = [msg]

        return [t for t in topics if len(t) > 1]