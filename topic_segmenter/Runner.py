import sys

from topic_segmenter.text.Message import Message
from topic_segmenter.grammar.MessageTokenizer import MessageTokenizer
from topic_segmenter.segmenter.ConversationSegmenter import ConversationSegmenter
from topic_segmenter.text.JSONParser import JSONParser


class Runner:
    def __init__(self, json_file_name):
        self.jsonFileName = json_file_name

    def run(self):
        parser = JSONParser(self.jsonFileName)
        self.messages = parser.getMessages()
        self.tokenizer = MessageTokenizer()
        windowSize = 3
        cosineSimilarityThreshold = 0.8
        segmenter = ConversationSegmenter(
            self.messages, windowSize, cosineSimilarityThreshold, self.tokenizer
        )
        return segmenter.segment()
        # self.report(topics)

    def report(self, topics):
        idGroups = []
        print("============================= detailed ========================")
        for topic in topics:
            print("== Topic ==")
            idGroup = []
            for message, reason in zip(topic.getMessages(), topic.getReasons()):
                idGroup.append(message.getID())
                print("\n\t------ id: \t" + str(message.getID()) + "\t" + reason)
                print("" + message.getText())
            print("\n")
            idGroups.append(idGroup)

        print("===============================")

        print("============================= short ========================")
        for topic in topics:
            print("== Topic ==")
            for message in topic.getMessages():
                print(str(message.getID()) + ":\t" + message.getText())
            print("\n")

        print(idGroups)
