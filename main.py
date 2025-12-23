from topic_segmenter.Runner import main
import nltk
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')
nltk.download('universal_tagset')

json_input = "raw_data/telegram_prepared.json"
main(json_input)
