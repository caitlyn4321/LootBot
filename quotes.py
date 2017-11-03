import random
import time
import datastore


class QuotesClass:
    filename = "quotes.json"

    def __init__(self, filename=""):
        """Initialize the quotes class"""
        if len(filename) > 0:
            self.filename = filename
        self.quotes_list = datastore.DataStore(self.filename)
        random.seed()

    def load(self, filename=""):
        """Load the JSON formatted quotes database"""
        if len(filename) == 0:
            filename = self.filename
        self.quotes_list.load(filename)

    def save(self, filename=""):
        """Save the JSON formatted quotes database"""
        if len(filename) == 0:
            filename = self.filename
        self.quotes_list.save(filename)

    def count(self):
        """Return a count of the quotes"""
        return len(self.quotes_list)

    def getindex(self):
        for index in range(1, len(self.quotes_list)):
            if str(index) not in self.quotes_list.keys():
                return index
        return len(self.quotes_list) + 1

    def add(self, quote):
        """Add a quote"""
        quote.append(time.time())
        index = self.getindex()
        self.quotes_list[str(index)] = quote
        self.quotes_list.save()
        return index

    def delete(self, num):
        """Delete a quote"""
        if str(num) in self.quotes_list.keys():
            del self.quotes_list[str(num)]
            self.save()
            return True
        else:
            return False

    def get_quote(self, num):
        """Return a specific quote"""
        if str(num) in self.quotes_list.keys():
            return self.quotes_list[str(num)] + [int(num)]
        else:
            return -1

    def get_random(self):
        """Get a random quote"""
        if len(self.quotes_list) >= 1:
            num = random.choice(list(self.quotes_list.keys()))
            return self.get_quote(num)
        else:
            return -1
