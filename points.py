import json
import threading
import time

# allowNegative - allow to go into negative with ur points account

POINTS_PER_CHATLVL = 5


class Points():
    def __init__(self, jsonpath):
        self.jsonpath = jsonpath
        self.elements = {}
        self.add_lock = threading.Lock()
        self.update_lock = threading.Lock()
        try:
            with open(self.jsonpath, 'r+') as file:
                self.elements = json.load(file)
        except Exception:
            pass
        self.pointsByLevel = [0]
        for level in range(1, 250):
            self.pointsByLevel.append(self.pointsByLevel[level - 1] + self.getPointsForLevelUp(level))

    def save(self, path=False):
        self.update_lock.acquire()
        if not path:
            path = self.jsonpath
        with open(path, 'w+') as file:
            json.dump(self.elements, file, indent=2)
            file.close()
        self.update_lock.release()

    def getFilePath(self):
        return self.jsonpath

    def reset(self):
        self.update_lock.acquire()
        self.elements = {}
        self.update_lock.release()

    def getPointsForLevelUp(self, level):
        if level <= 0:
            return 0
        return level * POINTS_PER_CHATLVL

    def getIdByName(self, name):
        for key in self.elements.keys():
            if self.elements[key]['n'] == name:
                return key
        return name

    def getById(self, id):
        return self.elements.get(id, self.__getNewDefault())

    def getPointsById(self, id):
        return self.getById(id).get('p', 0)

    def getLevelRemainingNextWithPoints(self, points):
        level = 0
        for pbl in self.pointsByLevel:
            if points < pbl:
                break
            level += 1
        remaining = points - self.pointsByLevel[level - 1]
        toLevelUp = self.getPointsForLevelUp(level)
        return level, remaining, toLevelUp

    def getPointDataById(self, id):
        element = self.getById(id)
        level, remaining, toLevelUp = self.getLevelRemainingNextWithPoints(element.get('p', 0))
        return {
            'n': element.get('n', '-'),
            'p': element.get('p', 0),
            'level': level,
            'points': remaining,
            'tonext': toLevelUp - remaining,
            'chatroulette': element.get('chatroulette', False),
            'chatpoker': element.get('chatpoker', False),
            'chattip': element.get('chattip', False),
            'questions': element.get('questions', False),
        }

    def setOnJoinMsgById(self, id, msg, writeStrength=2, announcementStrength=2, delete=False):
        # top5 ladder has announcement strength 3 and will thus "win" over a set message
        ws = self.getById(id).get('on_join_msg', {}).get('writeStrength', 0)
        if writeStrength >= ws:
            if delete:
                self.elements[id]['on_join_msg'] = False
                del self.elements[id]['on_join_msg']
            else:
                self.elements[id]['on_join_msg'] = {
                    'msg': msg,
                    'writeStrength': writeStrength,
                    'announcementStrength': announcementStrength,
                }
            return True
        return False

    def getOnJoinMsgById(self, id):
        oj = self.getById(id).get('on_join_msg', {})
        return oj.get('msg', False), oj.get('announcementStrength', 0)

    def addNew(self, id, name=False, data={}):
        """
        :param id: id of new element, will become name unless specified otherwise
        :param data: non default values
        """
        self.add_lock.acquire()
        if not name:
            name = id
        self.elements[id] = self.__getNewDefault(name)
        for key in data.keys():
            self.elements[id][key] = data[key]
        self.add_lock.release()

    def addNewIfNotExisting(self, id, name=False, data={}):
        if not self.elements.get(id, False):
            self.addNew(id, name=name, data=data)
        return self.elements[id]

    def __getNewDefault(self, name="-"):
        return {
            'n': name,         # name
            'p': 0,            # points
            't': time.time()   # time of last update
        }

    def updateById(self, id, data={}, delta={}, allowNegative=False, partial=False):
        """
        Returns false if delta causes a param to go <0
        :param id:
        :param data:
        :param delta:
        :return:
        """
        self.update_lock.acquire()
        if not self.elements.get(id, False):
            self.addNew(id)
        self.addNewIfNotExisting(id, data={})
        for key in data.keys():
            self.elements[id][key] = data[key]
        self.elements[id]['t'] = time.time()
        for key in delta.keys():
            new_value = self.elements[id].get(key, 0) + delta[key]
            if (new_value < 0) and (not allowNegative):
                if partial:
                    self.elements[id][key] = 0
                self.update_lock.release()
                return False
            self.elements[id][key] = new_value
            #if (new_value == 0):
            #    del self.elements[id][key]
        self.update_lock.release()
        return True

    def updatePointsById(self, id, points, partial=False):
        return self.updateById(id, delta={'p': points}, allowNegative=False, partial=partial)

    def transferBetweenKeysById(self, id, keyFrom, keyTo, amount, partial=False):
        """
        will not go negative
        """
        prevValue = self.addNewIfNotExisting(id).get(keyFrom, 0)
        if ((prevValue - amount) < 0):
            if (not partial):
                return False, 0
            amount = prevValue
        self.update_lock.acquire()
        self.elements[id][keyFrom] -= amount
        self.elements[id][keyTo] = self.elements[id].get(keyTo, 0) + amount
        self.update_lock.release()
        return True, amount

    def transferBetweenKeysForAll(self, keyFrom, keyTo, amount, deleteOld=True):
        """

        :param keyFrom:
        :param keyTo: False/None if only deleting old values
        :param amount: will be partially transfered by default, as much as possible
        :param deleteOld: removes old key from the dict
        :return:
        """
        self.update_lock.acquire()
        for id in self.elements.keys():
            if keyTo:
                p = min([amount, self.elements[id].get(keyFrom, 0)])
                self.elements[id][keyTo] = self.elements[id].get(keyTo, 0) + p
                self.elements[id][keyFrom] = 0
            if deleteOld and self.elements[id].get(keyFrom, 0) <= 0:
                del self.elements[id][keyFrom]
        self.update_lock.release()

    def transferByIds(self, receiverId, giverIdDict, receiverKey='p', giverKey='p', allowNegative=False, partial=False):
        """
        Will do only partial transfer if single giver fail to hand in

        :param receiverId:
        :param giverIdDict: {id1 : 5, id2 : 10, ...}
        :param receiverKey:
        :param giverKey:
        :return:
        """
        toTransfer = 0
        for giverId in giverIdDict.keys():
            if self.updateById(giverId, delta={giverKey: -giverIdDict[giverId]}, allowNegative=allowNegative, partial=partial):
                toTransfer += giverIdDict[giverId]
        #print('transfering', toTransfer, 'to', receiverId, ', with key', receiverKey) # TODO remove
        self.updateById(receiverId, delta={receiverKey: toTransfer}, allowNegative=True)
        return toTransfer

    def transferPointsByIds(self, receiverId, giverIdDict):
        return self.transferByIds(receiverId, giverIdDict)

    def transferPointsByIdsSimple(self, receiverId, giverId, points, partial=True, addTo=False):
        """
        :param receiverId:
        :param giverId:
        :param points: number or 'all'
        :param partial:
        :return: if something was transfered, amount transfered
        """
        p = points
        if p == 'all':
            p = 9999999999999999
        if type(p) == str:
            return False, 0
        if partial:
            p = min([p, self.getPointsById(giverId)])
        if self.updatePointsById(giverId, -p):
            self.updatePointsById(receiverId, p)
            if addTo:
                self.updateById(giverId, delta={addTo: -p}, allowNegative=True)
                self.updateById(receiverId, delta={addTo: p}, allowNegative=True)
            return p > 0, p
        return False, p

    def getSortedBy(self, by='p', reversed=True):
        return sorted([(k, self.elements[k].get(by, 0)) for k in self.elements.keys()], reverse=reversed, key=lambda v: v[1])

    def getSortedByMultiple(self, byPositive=['p'], byNegative=[], reversed=True):
        return sorted(
            [(k, sum([self.elements[k].get(bp, 0) for bp in byPositive]) - sum([self.elements[k].get(bp, 0) for bp in byNegative]))
            for k in self.elements.keys()], reverse=reversed, key=lambda v: v[1])

    def merge(self, mergeRemainingId, mergeRemovedId):
        self.update_lock.acquire()
        remaining = self.addNewIfNotExisting(mergeRemainingId)
        remainingName = remaining['n']
        removed = self.addNewIfNotExisting(mergeRemovedId)
        for key in removed.keys():
            # try adding first (points, stats), otherwise replace (strings, e.g. onjoin message)
            try:
                remaining[key] = remaining.get(key, 0) + removed[key]
            except Exception:
                remaining[key] = removed[key]
        remaining['n'] = remainingName
        del self.elements[mergeRemovedId]
        self.update_lock.release()

    """
    def getByName(self, name):
        return self.elements.get(self.getIdByName(name), self.__getNewDefault(name=name))

    def updatePointsByName(self, name, points):
        return self.updateByName(name, delta={'p' : points}, allowNegative=False)

    def transferByNames(self, receiverName, giverNameDict, receiverKey='p', giverKey='p'):
        idDict = {}
        for giverName in giverNameDict.keys():
            idDict[self.getIdByName(giverName)] = giverNameDict[giverName]
        return self.transferByIds(self.getIdByName(receiverName), idDict, receiverKey=receiverKey, giverKey=giverKey)

    def transferPointsByNames(self, receiverName, giverNameDict):
        return self.transferByNames(receiverName, giverNameDict)

    def updateByName(self, name, data={}, delta={}):
        return self.updateById(self.getIdByName(name), data=data, delta=delta)
    """
