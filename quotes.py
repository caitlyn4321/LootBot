import random,json, time

class quotesClass:
    quotes_list=[]
    filename="quotes.json"

    def __init__(self,filename=""):
        """Initialize the quotes class"""
        if len(filename)>0:
            self.filename=filename
        self.load(filename)
        random.seed()

    def load(self,filename=""):
        """Load the JSON formatted quotes database"""
        if len(filename)==0:
            filename=self.filename
        try:
            with open(filename) as json_data_file:
                self.quotes_list = json.load(json_data_file)
        except:
            return

    def save(self,filename=""):
        """Save the JSON formatted quotes database"""
        if len(filename)==0:
            filename=self.filename
        with open(filename, 'w') as outfile:
            json.dump(self.quotes_list, outfile)

    def count(self):
        """Return a count of the quotes"""
        return len(self.quotes_list)

    def add(self,quote):
        """Add a quote"""
        quote.append(time.time())
        self.quotes_list.append(quote)
        self.save()
        return self.count()

    def delete(self,num):
        """Delete a quote"""
        if 0 <= num and num <= self.count():
            del self.quotes_list[num-1]
            self.save()
            return True
        else:
            return False

    def get_quote(self,num):
        """Return a specific quote"""
        if 1 <= num and num <= self.count():
            return self.quotes_list[num-1]+[num]
        else:
            return -1

    def get_random(self):
        """Get a random quote"""
        if self.count()>1:
            num=random.randrange(1,self.count()+1)
            return self.get_quote(num)
        if self.count() > 0:
            return self.get_quote(1)
        else:
            return -1