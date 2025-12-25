from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from .topic_segmentor import TopicSegmentor, Topic, ChatMessage
from .window_topic_model import WindowTopicModel


@dataclass
class HybridTimeGapMLTopicSegmentor(TopicSegmentor):
    """
    1) Split messages into coarse "sessions" by time gap (bigger gap allowed).
    2) Inside each session generate sliding windows of size topic_size.
    3) Score each window by ML model P(single-topic).
    4) Select non-overlapping windows greedily by time, keeping only windows with proba >= threshold.
    """
    max_gap_seconds: int = 15 * 60
    threshold: float = 0.7
    tfidf_path: str = "models/tfidf_feat.joblib"
    model_path: str = "models/gbdt_topic_window.joblib"

    def __init__(
        self,
        max_gap_seconds: int,
        topic_size: int = 4,
        threshold: float = 0.7,
        tfidf_path: str = "models/tfidf_feat.joblib",
        model_path: str = "models/gbdt_topic_window.joblib",
    ):
        super().__init__(topic_size)
        self.max_gap_seconds = max_gap_seconds
        self.threshold = threshold
        self.tfidf_path = tfidf_path
        self.model_path = model_path
        self._model = WindowTopicModel.load(tfidf_path, model_path, topic_size=topic_size)

    def _split_sessions(self, messages: List[ChatMessage]) -> List[List[ChatMessage]]:
        if not messages:
            return []
        sessions: List[List[ChatMessage]] = []
        cur = [messages[0]]
        for m in messages[1:]:
            if (m.timestamp - cur[-1].timestamp) <= self.max_gap_seconds:
                cur.append(m)
            else:
                sessions.append(cur)
                cur = [m]
        sessions.append(cur)
        return sessions

    @staticmethod
    def _windows(msgs: List[ChatMessage], k: int) -> List[Tuple[int, List[ChatMessage]]]:
        out = []
        for i in range(0, len(msgs) - k + 1):
            out.append((i, msgs[i : i + k]))
        return out

    def _select_non_overlapping(
        self, scored: List[Tuple[int, float, List[ChatMessage]]]
    ) -> List[Topic]:
        """
        scored: list of (global_start_index, proba, window)
        We want windows that do not overlap in message indices.
        Greedy by time: sort by window end timestamp, accept if no overlap.
        """
        if not scored:
            return []

        scored.sort(key=lambda x: x[2][-1].timestamp)

        used_ids = set()
        picked: List[Topic] = []
        for _, p, w in scored:
            if p < self.threshold:
                continue
            ids = [m.id for m in w if hasattr(m, "id")]
            if not ids:
                ids = [hash((m.user, m.text, m.timestamp)) for m in w]

            if any(i in used_ids for i in ids):
                continue

            picked.append(w)
            used_ids.update(ids)

        return picked

    def get_topics(self, path: str) -> List[Topic]:
        messages = self.load_messages(path)
        if not messages:
            return []

        k = self.get_topic_size()
        sessions = self._split_sessions(messages)

        all_scored: List[Tuple[int, float, List[ChatMessage]]] = []
        global_offset = 0

        for sess in sessions:
            for local_i, w in self._windows(sess, k):
                p = self._model.predict_proba_single_topic(w)
                all_scored.append((global_offset + local_i, p, w))
            global_offset += len(sess)

        topics = self._select_non_overlapping(all_scored)
        return topics