import json
import threading
import time


class Events():
    def __init__(self, jsonpath):
        self.jsonpath = jsonpath
        self.events = {}
        self.lock = threading.Lock()
        try:
            with open(self.jsonpath, 'r+') as file:
                self.events = json.load(file)
        except Exception:
            pass

    def addEventFile(self, jsonpath):
        try:
            with open(jsonpath, 'r+') as file:
                newevents = json.load(file)
                for key in newevents.keys():
                    if not self.events.get(key):
                        self.events[key] = []
                    self.events[key].extend(newevents[key])
                    print('extended', key, 'by', len(newevents[key]), 'elements')
            return True
        except Exception:
            pass
        return False

    def save(self, path=False):
        self.lock.acquire()
        if not path:
            path = self.jsonpath
        with open(path, 'w+') as file:
            json.dump(self.events, file, indent=2)
            file.close()
        self.lock.release()

    def getFilePath(self):
        return self.jsonpath

    def reset(self):
        self.lock.acquire()
        self.events = {}
        self.lock.release()

    def addEvent(self, key, data):
        self.lock.acquire()
        if not self.events.get(key, False):
            self.events[key] = []
        data['t'] = time.time()
        self.events[key].append(data)
        self.lock.release()

    def getData(self, key):
        return self.events.get(key, []) + []

    def getFormattedChattips(self, key, name):
        eventdata = self.getData(key)
        tips = {}
        for tip in eventdata:
            giver, taker, p = tip.get('giver', '?'), tip.get('taker', '?'), tip.get('points', 0)
            if name == taker:
                tips[giver] = tips.get(giver, 0) + p
            if name == giver:
                tips[taker] = tips.get(taker, 0) - p
        return tips

    def getFormattedRouletteData(self, key, filtername=False, minparticipants=2):
        eventdata = self.getData(key)
        if filtername:
            i = 0
            while i < len(eventdata):
                game = eventdata[i]
                if game['bets'].get(filtername, False):
                    i += 1
                else:
                    eventdata.pop(i)
        if minparticipants:
            i = 0
            while i < len(eventdata):
                game = eventdata[i]
                if len(game['bets']) >= minparticipants:
                    i += 1
                else:
                    eventdata.pop(i)
        if len(eventdata) == 0:
            return {}
        gamecount = max([len(eventdata), 1])
        totalpoints = 0
        highestwin, highestwinner = 0, ""
        roibet, roiwin, roiratio, roiwinner = 0, 1, 0, ""
        for game in eventdata:
            gametotal = sum(game['bets'].values())
            totalpoints += gametotal
            gamewinner = game['winner']
            gameroiratio = gametotal / game['bets'].get(gamewinner, 999999999)
            if gametotal > highestwin:
                highestwin = gametotal
                highestwinner = gamewinner
            if (gameroiratio > roiratio):
                roiratio = gameroiratio
                roibet = game['bets'].get(game['winner'], 999999999)
                roiwin = gametotal
                roiwinner = gamewinner
        return {
            "count": str(gamecount),
            "totalpoints": str(totalpoints),
            "avg": format(totalpoints / gamecount, '.1f'),
            "hpoints": str(highestwin),
            "hwinner": highestwinner,
            "roibet": str(roibet),
            "roiwin": str(roiwin),
            "roiratio": format(roiratio, '.3f'),
            "roiwinner": roiwinner,
        }

    def getFormattedPokerData(self, key, filtername=False, minparticipants=2, winningtype=False):
        eventdata = self.getData(key)
        if filtername:
            i = 0
            while i < len(eventdata):
                game = eventdata[i]
                if game['losers'].get(filtername, False) or game['winners'].get(filtername, False):
                    i += 1
                else:
                    eventdata.pop(i)
        if minparticipants:
            i = 0
            while i < len(eventdata):
                game = eventdata[i]
                if (len(game['losers']) + len(game['winners'])) >= minparticipants:
                    i += 1
                else:
                    eventdata.pop(i)
        if winningtype:
            i = 0
            while i < len(eventdata):
                game = eventdata[i]
                if (game['winningtype'] == winningtype):
                    i += 1
                else:
                    eventdata.pop(i)
        if len(eventdata) == 0:
            return {}
        gamecount = max([len(eventdata), 1])
        totalpoints = 0
        highestwin, highestwinner = 0, []
        for game in eventdata:
            gametotal = sum(game['winners'].values()) + sum(game['losers'].values())
            totalpoints += gametotal
            gamewinners = game['winners']
            if gametotal > highestwin:
                highestwin = gametotal
                highestwinner = [k for k in gamewinners.keys()]
        return {
            "count": str(gamecount),
            "totalpoints": str(totalpoints),
            "avg": format(totalpoints / gamecount, '.1f'),
            "hpoints": str(highestwin),
            "hwinners": highestwinner,
        }

    def getFormattedQuestionData(self, key):
        eventdata = self.getData(key)
        if len(eventdata) == 0:
            return {}
        count = max([len(eventdata), 1])
        totalpoints = 0
        for question in eventdata:
            totalpoints += question.get('p', 0)
        return {
            "count": str(count),
            "totalpoints": str(totalpoints),
            "avg": format(totalpoints / count, '.1f'),
        }
