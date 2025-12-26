from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .topic_segmentor import TopicSegmentor, Topic, ChatMessage


@dataclass
class ReplyChainTopicSegmentor(TopicSegmentor):
    """
    Heuristic:
    Build topics from reply chains.

    For each message that replies to another message, we treat it as a candidate response.
    We follow reply_to_id backward to collect context messages.
    If we can collect exactly topic_size messages (context + response) -> emit a Topic.
    """
    def __init__(
        self,
        topic_size: int = 4,
        max_chain_hops: int = 50,
        non_overlapping: bool = True,
    ):
        super().__init__(topic_size)
        self._max_chain_hops = max_chain_hops
        self._non_overlapping = non_overlapping

    def _build_candidate_window(
        self,
        resp: ChatMessage,
        by_id: Dict[int, ChatMessage],
        topic_size: int,
    ) -> Optional[Topic]:
        if resp.reply_to_id is None:
            return None

        chain: List[ChatMessage] = [resp]
        cur: Optional[ChatMessage] = resp
        hops = 0

        while cur is not None and cur.reply_to_id is not None and hops < self._max_chain_hops:
            parent = by_id.get(cur.reply_to_id)
            if parent is None:
                break
            chain.append(parent)
            cur = parent
            hops += 1

        chain.reverse()

        if len(chain) < topic_size:
            return None

        window = chain[-topic_size:]

        if any(window[i].timestamp > window[i + 1].timestamp for i in range(len(window) - 1)):
            return None

        ids = [m.id for m in window]
        if len(set(ids)) != len(ids):
            return None

        return window

    def get_topics(self, path: str) -> List[Topic]:
        messages = self.load_messages(path)
        if not messages:
            return []

        by_id: Dict[int, ChatMessage] = {m.id: m for m in messages}
        topic_size = self.get_topic_size()

        candidates: List[Tuple[int, Topic]] = []
        for resp in messages:
            window = self._build_candidate_window(resp, by_id, topic_size)
            if window is None:
                continue
            end_ts = window[-1].timestamp
            candidates.append((end_ts, window))

        # earliest responses first
        candidates.sort(key=lambda x: x[0])

        if not self._non_overlapping:
            seen = set()
            out: List[Topic] = []
            for _, w in candidates:
                sig = tuple(m.id for m in w)
                if sig in seen:
                    continue
                seen.add(sig)
                out.append(w)
            return out

        # greedy select non-overlapping windows
        used_ids = set()
        picked: List[Topic] = []
        seen_sigs = set()

        for _, window in candidates:
            sig = tuple(m.id for m in window)
            if sig in seen_sigs:
                continue
            seen_sigs.add(sig)

            ids = [m.id for m in window]
            if any(mid in used_ids for mid in ids):
                continue

            picked.append(window)
            used_ids.update(ids)

        return picked