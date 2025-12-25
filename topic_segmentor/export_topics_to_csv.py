from typing import List
from topic_segmentor import Topic
import csv


def export_topics_to_csv(filename: str, topics: List[Topic]):
    topic_size = len(topics[0])
    if topic_size < 2:
        raise ValueError("topic size must be >= 2")

    for i, t in enumerate(topics):
        if len(t) != topic_size:
            raise ValueError(
                f"Topic at index {i} has size {len(t)}, expected {topic_size}"
            )

    context_size = topic_size - 1

    header = (
        [f"context_{i}" for i in range(context_size, 0, -1)]
        + ["response"]
    )

    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        for topic in topics:
            texts = [msg.text for msg in topic]

            response = texts[-1]
            contexts = list(reversed(texts[:-1]))

            writer.writerow(contexts + [response])