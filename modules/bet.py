import json

useDebugPrint = False


class Bets():
    def __init__(self, bot, chatpointsObj, chateventsObj, jsonpath):
        self.bot = bot
        self.chatpointsObj = chatpointsObj
        self.chateventsObj = chateventsObj
        self.jsonpath = jsonpath
        self.bets = {}
        try:
            with open(self.jsonpath, 'r+') as file:
                storedBets = json.load(file).get('bets', {})
                for key in storedBets.keys():
                    self.bets[key] = Bet(key, '', '')
                    self.bets[key].recoverFromDict(storedBets[key])
        except Exception:
            pass

    def count(self):
        return len(self.bets.keys())

    def asStrings(self):
        return [self.bets[key].asString() for key in self.bets.keys()]

    def createBet(self, name, description, channel='#shadows'):
        if self.betExists(name):
            return False
        self.bets[name] = Bet(name, description, channel)

    def betExists(self, name):
        return not (self.bets.get(name, False) == False)

    def closeBet(self, name):
        if self.betExists(name):
            return self.bets.get(name).closeBet(self)
        return False

    def addOptions(self, name, TEXT):
        if self.betExists(name):
            return self.bets.get(name).addOptions(self, TEXT)
        return False

    def addBet(self, name, channel, optionname, id, points, allpoints=False, printInChat=True):
        if self.betExists(name):
            return self.bets.get(name).addBet(self, channel, optionname, id, points, allpoints, printInChat)
        return False

    def reset(self):
        self.bets = {}

    def endBet(self, name, winningoption):
        reply = False
        if self.betExists(name):
            reply = self.bets.get(name).endBet(self, winningoption)
            self.bets[name] = False
            del self.bets[name]
        return reply

    def save(self, path=False):
        if not path:
            path = self.jsonpath
        with open(path, 'w+') as file:
            bets = {key: self.bets[key].__dict__ for key in self.bets.keys()}
            json.dump({'bets': bets}, file, indent=2)
            file.close()

    def getFilePath(self):
        return self.jsonpath


class Bet():
    def __init__(self, name, description, channel):
        self.name = name
        self.chatpointsDefaultKey = 'p'
        self.chatpointsReservedKey = 'chatbet-reserved'
        self.chatpointsStatisticsKey = 'chatbets'
        self.channel = channel
        self.gamecostreceiver = 'MAI'
        self.description = description
        self.options = {}
        self.openForBets = True

    def recoverFromDict(self, dct):
        self.name = dct.get('name')
        self.chatpointsDefaultKey = dct.get('chatpointsDefaultKey')
        self.chatpointsReservedKey = dct.get('chatpointsReservedKey')
        self.chatpointsStatisticsKey = dct.get('chatpointsStatisticsKey')
        self.channel = dct.get('channel')
        self.gamecostreceiver = dct.get('gamecostreceiver')
        self.description = dct.get('description')
        self.options = dct.get('options')
        self.openForBets = dct.get('openForBets')

    def __debugPrint(self, text):
        if useDebugPrint:
            print(text.encode('ascii', errors='backslashreplace'))

    def __outputToChat(self, main, channel, msg, ignore=False):
        if ignore:
            return
        self.__debugPrint(channel + ': ' + msg)
        main.bot.privmsg(channel, msg)

    def __addOptionIfNecessary(self, optionname):
        if not self.options.get(optionname, False):
            self.__debugPrint('adding option: ' + optionname)
            self.options[optionname] = {}

    def __addPlayerToOption(self, optionname, id, points):
        if points <= 0:
            return
        self.__addOptionIfNecessary(optionname)
        self.options[optionname][id] = self.options[optionname].get(id, 0) + points

    def __reservePlayerPoints(self, main, name, points, partial):
        return main.chatpointsObj.transferBetweenKeysById(name, self.chatpointsDefaultKey, self.chatpointsReservedKey, points, partial=partial)

    def closeBet(self, main):
        self.openForBets = False

    def addOptions(self, main, TEXT):
        for option in TEXT.lower().replace(",", " ").split():
            if len(option) >= 1:
                self.__addOptionIfNecessary(option)

    def asString(self):
        optionStrings = [key + " (" + format(sum(self.options[key].values()), '.1f') + ")" for key in self.options.keys()]
        return self.name + ": " + self.description + " [" + ", ".join(optionStrings) + "]"

    def addBet(self, main, channel, optionname, id, points, allpoints, printInChat):
        self.__debugPrint('adding bet: ' + optionname + ', id=' + id + ', points=' + str(points) + ', allpoints=' + str(allpoints))
        if not self.openForBets:
            self.__outputToChat(main, channel, 'Betting is closed!')
            return False
        if optionname not in self.options.keys():
            self.__outputToChat(main, channel, 'The selection option does not exist!')
            return False
        worked, amount = self.__reservePlayerPoints(main, id, points, partial=allpoints)
        if worked:
            self.__addPlayerToOption(optionname, id, amount)
            if allpoints:
                self.__outputToChat(main, channel, 'Noted! (' + format(amount, '.1f') + ' points)', ignore=(not printInChat))
            else:
                self.__outputToChat(main, channel, 'Noted!', ignore=(not printInChat))
            return True
        return False

    def endBet(self, main, winningoption):
        if (winningoption not in self.options.keys()):
            return False
        winning = {}
        all = {}
        for key in self.options.keys():
            option = self.options[key]
            if key == winningoption:
                for name in option.keys():
                    winning[name] = winning.get(name, 0) + option[name]
                    all[name] = all.get(name, 0) + option[name]
            else:
                for name in option.keys():
                    all[name] = all.get(name, 0) + option[name]
        winningpoints = sum(winning.values())
        losingpoints = sum(all.values())
        # first, all players send their lost points
        for name in all.keys():
            pointsLost = all[name]
            dct = {name: pointsLost}
            self.__debugPrint("Handling player " + name + ", sending " + str(pointsLost) + " points to gamecostreceiver")
            main.chatpointsObj.transferByIds(self.gamecostreceiver, dct, receiverKey=self.chatpointsDefaultKey, giverKey=self.chatpointsReservedKey, allowNegative=False, partial=False)
            main.chatpointsObj.transferByIds(self.gamecostreceiver, dct, receiverKey=self.chatpointsStatisticsKey, giverKey=self.chatpointsStatisticsKey, allowNegative=True, partial=False)
        # then winners get their proportional parts back
        for name in winning.keys():
            pointsWon = (winning[name] / winningpoints) * losingpoints
            pointsWon = int(pointsWon)
            dct = {self.gamecostreceiver: pointsWon}
            winning[name] = pointsWon
            self.__debugPrint("Handling winner " + name + ", sending " + str(pointsWon) + " points from gamecostreceiver")
            main.chatpointsObj.transferByIds(name, dct, receiverKey=self.chatpointsDefaultKey, giverKey=self.chatpointsDefaultKey, allowNegative=False, partial=False)
            main.chatpointsObj.transferByIds(name, dct, receiverKey=self.chatpointsStatisticsKey, giverKey=self.chatpointsStatisticsKey, allowNegative=True, partial=False)
        # stats
        main.chateventsObj.addEvent(self.chatpointsStatisticsKey, {
            'name': self.name,
            'description': self.description,
            'winners': winning,
            'bets': all,
        })
        # inform players
        for name in all.keys():
            self.__outputToChat(main, name, 'The bet "{name}" finished, winning option was "{winningoption}"! Your points changed by {diff}, you have a total of {total} points now.'.format(**{
                'name': self.name,
                'winningoption': winningoption,
                'diff': format(winning.get(name, 0) - all.get(name, 0), '.1f'),
                'total': format(main.chatpointsObj.getById(name).get(self.chatpointsDefaultKey, 0), '.1f'),
            }))
        # inform channel
        dct = {
            'name': self.name,
            'winningoption': winningoption,
            'points': format(losingpoints, '.1f'),
            'winnercount': str(len(winning.keys())),
            'count': str(len(all.keys())),
        }
        if len(winning.keys()) >= 1:
            self.__outputToChat(main, self.channel, 'The bet "{name}" finished, winning option was "{winningoption}"! {points} points are distributed to {winnercount} winners, from {count} participants!'.format(**dct))
        else:
            self.__outputToChat(main, self.channel, 'The bet "{name}" finished, winning option was "{winningoption}"! Nobody won any of the {points} points!'.format(**dct))
        return True
