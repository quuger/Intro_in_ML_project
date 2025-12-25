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
    __max_gap_seconds: int = 120

    def __init__(self, max_gap_seconds, topic_size=4):
        super().__init__(topic_size)
        self.__max_gap_seconds = max_gap_seconds

    def get_topics(self, path: str) -> List[Topic]:
        messages = self.load_messages(path)
        if not messages:
            return []

        topics: List[Topic] = []
        current: Topic = [messages[0]]

        for msg in messages[1:]:
            prev: ChatMessage = current[-1]

            time_ok = (msg.timestamp - prev.timestamp) <= self.__max_gap_seconds
            size_ok = len(current) < self.get_topic_size()

            if time_ok and size_ok:
                current.append(msg)
            else:
                if len(current) > 1:
                    topics.append(current)
                current = [msg]

        if len(current) > 1:
            topics.append(current)

        return [t for t in topics if len(t) == self.get_topic_size()]
    