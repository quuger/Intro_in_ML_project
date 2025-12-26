from topic_segmentor import HybridTimeGapMLTopicSegmentor, export_topics_to_csv

seg = HybridTimeGapMLTopicSegmentor(
    max_gap_seconds=300,
    topic_size=4,
    threshold=0.7,
    tfidf_path="models/tfidf_feat.joblib",
    model_path="models/gbdt_topic_window.joblib",
)

topics = seg.get_topics("raw_data/messages.json")
print("Obtained topics:", len(topics))

export_topics_to_csv("hybrid_sns.csv", topics)