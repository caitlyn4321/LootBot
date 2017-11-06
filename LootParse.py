import requests
import re
import html
import math
import static
from datetime import datetime


class LootParse:
    characters = {}
    fully_loaded = 0

    def __init__(self):
        """Startup of the loot parser.  Initial values"""
        self.reload()

    def reload(self):
        """Performs the actual reload of the character data"""
        try:

            req_api = requests.get('https://theancientcoalition.com/api.php?function=points&format=json').json()
            req_web = requests.get('https://theancientcoalition.com/index.php/Points/?show_twinks=1')

            self.characters = {}

            for character in req_api['players'].values():
                thischaracter = {"id": character["id"],
                                 'name': character['name'],
                                 'class': character['class_name'],
                                 'items': [],
                                 'items_loaded': 0}
                self.characters[character['name'].upper()] = thischaracter

            web_lines = req_web.text.splitlines()
            counter = 0

            while counter < len(web_lines):
                if "<td ><a href=\"/index.php/Character/" in web_lines[counter]:
                    m = re.search("(\w+)</a>", web_lines[counter])
                    charname = m.group(1)
                    attendance = []
                    p = re.compile("\">(.*)</td>")
                    m = p.search(web_lines[counter + 2])
                    self.characters[charname.upper()]['rank'] = m.group(1)
                    p = re.compile("(\d+)/(\d+)")
                    m = p.search(web_lines[counter + 3])
                    att = m.group(1, 2)
                    attendance.append([int(att[0]), int(att[1])])
                    m = p.search(web_lines[counter + 4])
                    att = m.group(1, 2)
                    attendance.append([int(att[0]), int(att[1])])
                    m = p.search(web_lines[counter + 5])
                    att = m.group(1, 2)
                    attendance.append([int(att[0]), int(att[1])])
                    self.characters[charname.upper()]['attendance'] = attendance
                    counter += 4
                counter += 1
            self.fully_loaded = 1
        except:
            self.fully_loaded = 0

    def is_loaded(self):
        """A function which allows outside functions to know whether the character database is loaded"""
        return self.fully_loaded

    def get_char(self, character):
        """Returns the raw data for a specific character"""
        self.cache_items(character)
        return self.characters[character.upper()]

    def cache_items(self, character):
        """Loads to loot table into the character table for a specific character"""
        if self.characters[character.upper()]['items_loaded'] == 1:
            return
        req_web = requests.get('https://theancientcoalition.com/index.php/Items/?search_type=buyer&search=' + character)
        counter = 0
        web_lines = req_web.text.splitlines()

        while counter < len(web_lines):
            if "<td class=\"hiddenSmartphone twinktd\">Items</td>" in web_lines[counter]:
                m = re.search("<td >(\w+)</td>", web_lines[counter - 3])
                charname = m.group(1).upper()

                newitem = {}
                if "img" in web_lines[counter - 2]:
                    m = re.search("> (.+)</span></a></td>", web_lines[counter - 2])
                else:
                    m = re.search("title=\"\w+\">\s?(.+)</span></a></td>", web_lines[counter - 2])
                newitem['name'] = html.unescape(m.group(1))
                m = re.search("\">(.+)</a></td>", web_lines[counter - 1])
                newitem['raid'] = html.unescape(m.group(1))
                m = re.search("<td >(.+)</td>", web_lines[counter - 4])
                raiddate = m.group(1)
                datetime_object = datetime.strptime(raiddate, '%m.%d.%y')
                newitem['date'] = datetime_object.date()
                self.characters[charname]['items'].append(newitem)
            counter += 1
        self.characters[character.upper()]['items_loaded'] = 1

    def test(self):
        """Performs the item loading test against the characters table"""
        for character in self.characters.keys():
            print(self.get_char(character))

    def display(self, character):
        """Returns a formatted output for the character data passed to it."""
        cache = self.get_char(character.upper())
        print("display: {}".format(character))
        output = "**{}** ({}/{})".format(cache['name'], cache['class'], cache['rank'])
        thirtyatt = int(cache['attendance'][0][0]) / int(cache['attendance'][0][1])
        emote = static.emotes['90']
        if thirtyatt < .9:
            emote = static.emotes['50']
        if thirtyatt <= .50:
            emote = static.emotes['35']
        if thirtyatt <= .35:
            emote = static.emotes['0_']
        output +="\t{} 30 Day: **{}% ({}/{})**"\
            .format(emote, math.ceil(100 * int(cache['attendance'][0][0]) / int(cache['attendance'][0][1])),
                    cache['attendance'][0][0], cache['attendance'][0][1])
        output += "\t60 Day: **{}% ({}/{})**"\
            .format(math.ceil(100 * int(cache['attendance'][1][0]) / int(cache['attendance'][1][1])),
                    cache['attendance'][1][0], cache['attendance'][1][1])
        output += "\tLifetime Day: **{}% ({}/{})**"\
            .format(math.ceil(100 * int(cache['attendance'][2][0]) / int(cache['attendance'][2][1])),
                    cache['attendance'][2][0], cache['attendance'][2][1])
        output += "\n\t__Items__: {}\n".format(len(cache['items']))
        for item in cache['items']:
            output += "\t\t{}\t{}\t{}\n".format(item['name'], item['raid'], item['date'].strftime("%d %B %y"))

        return output

    def classes(self, classtype):
        """Search the characters table for a list of names of those matching a class"""
        results = []
        for character in self.characters.values():
            doappend = ""
            if character['class'].upper() == classtype.upper():
                doappend = character['name']
            if "rank" in character.keys():
                if character['rank'].upper() == classtype.upper():
                    doappend = character['name']
            if len(doappend) > 0:
                results.append(doappend)
        return results
