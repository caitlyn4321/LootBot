import requests
import datetime

class EQServerStatus:
    url="https://census.daybreakgames.com/s:dgc/json/get/global/game_server_status?game_code=eq&name={}&c%3Ashow=name" \
        "%2Clast_reported_state%2Clast_reported_time"

    def __init__(self, servername="Agnarr"):
        """Initialize the class"""
        self._servername = servername
        self.loaded = 0
        self.state = ""
        self.time = 0
        self.lastchecked = 0
        self._update()
        self.minseconds = 10

    def _update(self):
        try:
            changed = False
            req_api = requests.get(self.url.format(self._servername)).json()

            if int(req_api['returned'])>0:
                if req_api['game_server_status_list'][0]['last_reported_state'] != self.state:
                    changed = True
                    self.state = req_api['game_server_status_list'][0]['last_reported_state']
                self.time = datetime.datetime.fromtimestamp(
                    int(req_api['game_server_status_list'][0]['last_reported_time']))
            else:
                changed = None
            self.lastchecked=datetime.datetime.now()
            self.loaded=1
            return changed
        except:
            self.loaded=0
            return None

    def check(self):
        if datetime.datetime.now() < self.lastchecked + datetime.timedelta(seconds=self.minseconds):
            return None
        return self._update()