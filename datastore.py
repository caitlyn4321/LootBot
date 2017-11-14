import json


class DataStore(dict):
    _filename = "data_local.json"

    def __init__(self, filename=""):
        """Initialize the DataStore class"""
        super(DataStore, self).__init__()
        if len(filename) > 0:
            self._filename = filename
        self.load(self._filename)

    def load(self, filename=""):
        """Load the JSON formatted database"""
        if len(filename) == 0:
            filename = self._filename
        try:
            with open(filename) as json_data_file:
                super(DataStore, self).update(json.load(json_data_file))
        except:
            pass

    def save(self, filename=""):
        """Save the JSON formatted database"""
        if len(filename) == 0:
            filename = self._filename
        with open(filename, 'w') as outfile:
            json.dump(self, outfile)
