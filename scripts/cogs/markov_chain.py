import random

class Word:
    def __init__(self, string):
        self.string = string
        self.starts = 0
        self.following_words = {"END": 0}

    def __hash__(self):
        return hash(self.string)

    def __eq__(self, other):
        return self.string == other.string

    def __str__(self):
        return self.string

    def add_occurance(self, word):
        if word is None:
            self.following_words["END"] += 1
            return
        if word not in self.following_words:
            self.following_words[word] = 0
        self.following_words[word] += 1

    def get_next_word(self):
        next_word = random.choice([word for word in self.following_words for y in range(self.following_words[word])])
        if isinstance(next_word, str):
            return None
        return next_word
