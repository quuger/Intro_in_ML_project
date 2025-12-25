from __future__ import annotations

from dataclasses import dataclass
from typing import List
import numpy as np
import joblib
from sklearn.metrics.pairwise import cosine_similarity

from .topic_segmentor import ChatMessage


@dataclass
class WindowTopicModel:
    """
    Predicts P(window is single-topic) for a fixed-size window (topic_size messages).
    Uses:
      - tfidf_feat: TfidfVectorizer
      - gbdt: any sklearn classifier with predict_proba
    """
    tfidf_feat: object
    gbdt: object
    topic_size: int = 4

    @classmethod
    def load(cls, tfidf_path: str, model_path: str, topic_size: int = 4) -> "WindowTopicModel":
        tfidf_feat = joblib.load(tfidf_path)
        gbdt = joblib.load(model_path)
        return cls(tfidf_feat=tfidf_feat, gbdt=gbdt, topic_size=topic_size)

    @staticmethod
    def _window_to_text(msgs: List[ChatMessage]) -> str:
        return "\n".join([f"{m.user}: {m.text}" for m in msgs])

    def _tfidf_cos(self, a: str, b: str) -> float:
        X = self.tfidf_feat.transform([a, b])
        return float(cosine_similarity(X[0], X[1])[0, 0])

    def featurize(self, msgs: List[ChatMessage]) -> np.ndarray:
        if len(msgs) != self.topic_size:
            raise ValueError(f"Expected window size {self.topic_size}, got {len(msgs)}")

        ctx = msgs[:-1]
        resp = msgs[-1]

        ctx_text = "\n".join([f"{m.user}: {m.text}" for m in ctx])
        resp_text = f"{resp.user}: {resp.text}"

        sim_ctx_resp = self._tfidf_cos(ctx_text, resp_text)

        dts = [max(0, msgs[i + 1].timestamp - msgs[i].timestamp) for i in range(len(msgs) - 1)]
        max_dt_neighbors = max(dts)
        dt_last = dts[-1]

        users = [m.user for m in msgs]
        num_unique_users = len(set(users))
        resp_user_seen = 1.0 if resp.user in [m.user for m in ctx] else 0.0

        question_in_last_context = 1.0 if "?" in ctx[-1].text else 0.0

        feats = np.array(
            [
                sim_ctx_resp,
                float(np.log1p(max_dt_neighbors)),
                float(np.log1p(dt_last)),
                float(num_unique_users),
                float(resp_user_seen),
                float(question_in_last_context),
            ],
            dtype=np.float32,
        )
        return feats

    def predict_proba_single_topic(self, msgs: List[ChatMessage]) -> float:
        x = self.featurize(msgs).reshape(1, -1)
        return float(self.gbdt.predict_proba(x)[0, 1])