import requests, re, html, math
from datetime import datetime


class LootParse:
    characters={}
    fully_loaded=0

    def __init__(self):
        self.reload()

    def reload(self):
        try:

            reqAPI = requests.get('https://theancientcoalition.com/api.php?function=points&format=json').json()
            reqWEB = requests.get('https://theancientcoalition.com/index.php/Points/?show_twinks=1')

            self.characters={}

            for character in reqAPI['players'].values():
                thischaracter={}
                thischaracter["id"]=character["id"]
                thischaracter['name'] = character['name']
                thischaracter['class'] = character['class_name']
                thischaracter['items'] = []
                self.characters[character['name'].upper()]=thischaracter

            webLines=reqWEB.text.splitlines()
            counter=0

            while counter<len(webLines):
                if "<td ><a href=\"/index.php/Character/" in webLines[counter]:
                    m=re.search("(\w+)</a>",webLines[counter])
                    charname=m.group(1)
                    attendance=[]
                    p = re.compile("\">(.*)</td>")
                    m = p.search(webLines[counter + 2])
                    self.characters[charname.upper()]['rank'] = m.group(1)
                    p = re.compile("(\d+)/(\d+)")
                    m = p.search(webLines[counter+3])
                    att=m.group(1,2)
                    attendance.append([int(att[0]),int(att[1])])
                    m = p.search( webLines[counter + 4])
                    att = m.group(1, 2)
                    attendance.append([int(att[0]), int(att[1])])
                    m = p.search( webLines[counter + 5])
                    att = m.group(1, 2)
                    attendance.append([int(att[0]), int(att[1])])
                    self.characters[charname.upper()]['attendance']=attendance
                    counter=counter+4
                counter=counter+1
            self.fully_loaded=1
        except:
            self.fully_loaded=0

    def is_loaded(self):
        return self.fully_loaded

    def getChar(self,character):
        self.cacheItems(character)
        return self.characters[character.upper()]

    def cacheItems(self,character):
        reqWEB = requests.get('https://theancientcoalition.com/index.php/Items/?search_type=buyer&search='+character)
        counter=0
        webLines = reqWEB.text.splitlines()

        while counter < len(webLines):
            if "<td class=\"hiddenSmartphone twinktd\">Items</td>" in webLines[counter]:
                m = re.search("<td >(\w+)</td>", webLines[counter-3])
                charname = m.group(1).upper()
                found=0

                for item in self.characters[charname]['items']:
                    m = re.search("> (.+)</span></a></td>", webLines[counter - 2])
                    if html.unescape(item['name']) == html.unescape(m.group(1)):
                        m = re.search("\">(.+)</a></td>", webLines[counter - 1])
                        item['raid']=html.unescape(m.group(1))
                        m = re.search("<td >(.+)</td>", webLines[counter - 4])
                        raiddate = m.group(1)
                        datetime_object = datetime.strptime(raiddate, '%m.%d.%y')
                        item['date']=datetime_object.date()
                        found=1

                if found==0:
                    newitem={}
                    m = re.search("> (.+)</span></a></td>", webLines[counter - 2])
                    newitem['name']=html.unescape(m.group(1))
                    m = re.search("\">(.+)</a></td>", webLines[counter - 1])
                    newitem['raid'] = html.unescape(m.group(1))
                    m = re.search("<td >(.+)</td>", webLines[counter - 4])
                    raiddate = m.group(1)
                    datetime_object = datetime.strptime(raiddate, '%m.%d.%y')
                    newitem['date'] = datetime_object.date()
                    self.characters[charname]['items'].append(newitem)
            counter = counter + 1

    def test(self):
        for character in self.characters.keys():
            print (self.getChar(character))

    def display(self,character):
        cache=self.getChar(character.upper())
        output="**"+cache['name']+"** ("+cache['class']+"/"+cache['rank']+")"
        output=output+"\t30 Day: **"+ str(math.floor(100*int(cache['attendance'][0][0])/int(cache['attendance'][0][1])))+"% ("+str(cache['attendance'][0][0])+"/"+str(cache['attendance'][0][1])+")**"
        output = output + "\t60 Day: **" + str(
            math.floor(100*int(cache['attendance'][1][0]) / int(cache['attendance'][1][1]))) + "% (" + \
                 str(cache['attendance'][1][0]) + "/" + str(cache['attendance'][1][1]) + ")**"
        output = output + "\tLifetime: **" + str(
            math.floor(100*int(cache['attendance'][2][0]) / int(cache['attendance'][2][1]))) + "% (" + \
                 str(cache['attendance'][2][0]) + "/" + str(cache['attendance'][2][1]) + ")**"
        output=output+"\n\tItems: "+str(len(cache['items']))+"\n"
        for item in cache['items']:
            output=output+"\t\t"+item['name']+"\t"+item['raid']+"\t"+item['date'].strftime("%d %B %y")+"\n"

        return output

    def classes(self,classtype):
        results=[]
        for character in self.characters.values():
            if character['class'].upper() == classtype.upper():
                results.append(character['name'])
        return results
