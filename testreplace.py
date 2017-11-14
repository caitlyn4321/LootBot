import time
import datastore


class WordResponse:
    filename = "data_responses.json"

    def __init__(self, filename=""):
        """Initialize the quotes class"""
        if len(filename) > 0:
            self.filename = filename
        self.response_list = datastore.DataStore(self.filename)

    def load(self, filename=""):
        """Load the JSON formatted quotes database"""
        if len(filename) == 0:
            filename = self.filename
        self.response_list.load(filename)

    def save(self, filename=""):
        """Save the JSON formatted quotes database"""
        if len(filename) == 0:
            filename = self.filename
        self.response_list.save(filename)

    def count(self):
        """Return a count of the quotes"""
        return len(self.response_list)

    def add(self, word: str, phrase):
        """Add a quote"""
        self.response_list[word.upper()] = ' '.join(list(phrase))
        self.response_list.save()

    def delete(self, word: str):
        """Delete a quote"""
        if word.upper() in self.response_list.keys():
            del self.response_list[word.upper()]
            self.save()
            print(self.response_list)
            return True
        else:
            return False

    def check(self, *words: str):
        """Return a specific quote"""
        for word in self.response_list.keys():
            if word.upper() in ''.join(words).upper():
                return self.response_list[word.upper()]
            else:
                return None
