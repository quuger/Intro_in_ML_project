# from topic_segmenter.Runner import main
# import nltk
# nltk.download('punkt_tab')
# nltk.download('averaged_perceptron_tagger_eng')
# nltk.download('universal_tagset')

# json_input = "raw_data/telegram_prepared.json"
# main(json_input)

from topic_segmentor import TimeGapTopicSegmentor

seg = TimeGapTopicSegmentor(max_gap_seconds=120)
topics = seg.get_topics("raw_data/messages.json")

print(f"Obtained topics count: {len(topics)}")

print("Topic messages:")
for t in topics:
    for msg in t:
        print(f"{msg.user}: {msg.text}")
    print("\n\n")
