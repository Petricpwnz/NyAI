# import json
import os
import numpy as np
from points import Points
from events import Events
import matplotlib.pyplot as plt

pltSavePath = "plots/"
pltSave = True
pltShow = True
plt.figure(figsize=(18, 6))


def savePlt(string):
    if plt and pltSave:
        plt.savefig("./" + pltSavePath + string.replace(':', '') + '.png')
        plt.clf()
        plt.cla()


def showPlt():
    if plt and pltShow:
        plt.show()


def plotPointsByLevel(chatpointsObj, points):
    yToNextLevel, yLevel = [], []
    for p in points:
        level, remaining, toNext = chatpointsObj.getLevelRemainingNextWithPoints(p)
        yToNextLevel.append(toNext)
        yLevel.append(level)
    plt.plot(points, yLevel, 'b')
    #plt.plot(points, yToNextLevel, 'r')
    plt.xlabel("Points")
    plt.ylabel("")
    plt.hlines([10 * i for i in range(11)], points[0], points[-1])
    plt.legend(['Level'])
    savePlt('Level')
    showPlt()


def getFormattedList(lst, firstElements=5, lastElements=5, groupRest=True, average=False, sort=True):
    if len(lst) == 0:
        return []
    if sort:
        lst = sorted(lst, reverse=True, key=lambda v: v[1])
    avg = []
    if average:
        avg = [('Average (' + str(len(lst)) + ')', sum(v[1] for v in lst) / len(lst))]
    lstTop = lst[:firstElements]
    lst = lst[firstElements:]
    bottomStart = max([(len(lst) - lastElements), 0])
    lstBottom = lst[bottomStart:]
    lstRest = lst[:bottomStart]
    lst = lstTop
    if len(lstRest) > 0 and groupRest:
        lst.append(('Others (' + str(len(lstRest)) + ')', sum(v[1] for v in lstRest)))
    lst += avg
    lst += lstBottom
    return lst


def plotListAsHist(lst, legendString):
    if len(lst) == 0:
        return
    x = np.arange(len(lst))
    plt.bar(x, height=[lst[i][1] for i in range(len(x))])
    plt.xticks(x, [lst[i][0] for i in range(len(x))])
    plt.hlines([0], x[0] - 0.5, x[-1] + 0.5)
    plt.legend([legendString])
    savePlt(legendString)
    showPlt()


def plotChattipsForName(chateventsObj, name, firstElements=5, lastElements=5):
    tippers = {}
    for tip in chateventsObj.getData('chattip'):
        if tip.get('taker', '') == name:
            tippers[tip['giver']] = tippers.get(tip['giver'], 0) + tip['points']
        if tip.get('giver', '') == name:
            tippers[tip['taker']] = tippers.get(tip['taker'], 0) - tip['points']
    plotListAsHist(getFormattedList([(k, tippers.get(k, 0)) for k in tippers.keys()], firstElements=firstElements, lastElements=lastElements), name + "'s sponsors")


def getRouletteData(chateventsObj):
    data = {}
    for game in chateventsObj.getData('chatroulette'):
        bets = game['bets']
        gametotal = sum(bets.values())
        for name in bets.keys():
            data[name] = data.get(name, 0) - bets[name]
        data[game['winner']] = data.get(game['winner'], 0) + gametotal
    return [(key, data[key]) for key in data.keys()]


def getPokerData(chateventsObj):
    data = {}
    for game in chateventsObj.getData('chatpoker'):
        for player in game.get('losers').keys():
            data[player] = data.get(player, 0) - game['losers'][player]
        for player in game.get('winners').keys():
            data[player] = data.get(player, 0) - game['winners'][player] + game.get('stakepw', 0)
    return [(key, data[key]) for key in data.keys()]


def filterChannels(lst):
    filteredLst = []
    for element in lst:
        if element[0].startswith('#'):
            continue
        filteredLst.append(element)
    return filteredLst


def plotMost(chatpointsObj, legendString, by='p', ignoreChannels=True, firstElements=10, lastElements=0, reversed=True, average=False):
    ladder = chatpointsObj.getSortedBy(by, reversed=reversed)
    if ignoreChannels:
        plotListAsHist(getFormattedList(filterChannels(ladder), firstElements=firstElements, lastElements=lastElements, average=average), legendString + " (no channels)")
        return
    plotListAsHist(getFormattedList(ladder, firstElements=firstElements, lastElements=lastElements, average=average), legendString)


def plotMostPoints(chatpointsObj, ignoreChannels=True, firstElements=10):
    return plotMost(chatpointsObj, "Most points", by='p', ignoreChannels=ignoreChannels, firstElements=firstElements)


def plotGamblersTipreceivers(chatpointsObj, ignoreChannels=True, firstElements=10, reversed=False):
    ladder = chatpointsObj.getSortedByMultiple(byPositive=['chatroulette', 'chattip'], byNegative=[], reversed=reversed)
    legendString = "Tips + roulette"
    if ignoreChannels:
        plotListAsHist(getFormattedList(filterChannels(ladder), firstElements=firstElements, lastElements=0, groupRest=False, sort=False), legendString + " (no channels)")
        return
    plotListAsHist(getFormattedList(ladder, firstElements=firstElements, lastElements=0, groupRest=False, sort=False), legendString)


def plotPointsWithoutInfluence(chatpointsObj, ignoreChannels=True, firstElements=10, lastElements=0, reversed=False):
    ladder = chatpointsObj.getSortedByMultiple(byPositive=['p'], byNegative=['chatroulette', 'chattip'], reversed=reversed)
    legendString = "Points-(Tips+Roulette)"
    if ignoreChannels:
        plotListAsHist(getFormattedList(filterChannels(ladder), firstElements=firstElements, lastElements=lastElements, groupRest=False, sort=False, average=True), legendString + " (no channels)")
        return
    plotListAsHist(getFormattedList(ladder, firstElements=firstElements, lastElements=lastElements, groupRest=False, sort=False), legendString)


path = '/backups/reset/1/1503159466'
path = '/backups/reset/2/1503403069'
path = ""
chatevents = Events("." + path + "/chatevents.json")
allchatevents = Events("." + path + "/chatevents.json")
for dirname, dirnames, filenames in os.walk('./backups/reset/'):
    print(dirnames)
    for filename in filenames:
        if filename == 'chatevents.json':
            print(dirname + '/' + filename)
            allchatevents.addEventFile(dirname + '/' + filename)
chatpoints = Points("." + path + "/chatlevel.json")
chatpoints.save()

#plotChattipsForName(chatevents, 'jarikboygangela')
#plotChattipsForName(chatevents, 'MAI')
#plotMost(chatpoints, "Chatroulette ", by='chatroulette', firstElements=6, lastElements=6, ignoreChannels=True, average=True)
#plotGamblersTipreceivers(chatpoints, ignoreChannels=True, reversed=True)

pltShow = False
pltSave = True
if True:
    plotMostPoints(chatpoints, firstElements=10, ignoreChannels=True)
    plotPointsWithoutInfluence(chatpoints, ignoreChannels=True, reversed=True)
    plotChattipsForName(chatevents, '#reset', firstElements=6, lastElements=0)
    plotMost(chatpoints, "Chattips", by='chattip', firstElements=5, lastElements=5, ignoreChannels=False)
    plotMost(chatpoints, "Chatpoker", by='chatpoker', firstElements=5, lastElements=5, ignoreChannels=False)
    plotMost(chatpoints, "Chatroulette", by='chatroulette', firstElements=5, lastElements=5, ignoreChannels=True)
    plotMost(chatpoints, "Chatpoker tourney", by="pokertourney", firstElements=5, lastElements=5, ignoreChannels=False)
    # of all events
    plotListAsHist(getFormattedList(getRouletteData(allchatevents), firstElements=5, lastElements=5, groupRest=True, average=False, sort=True), "Chatroulette data, all epochs")
    plotListAsHist(getFormattedList(getRouletteData(chatevents), firstElements=5, lastElements=5, groupRest=True, average=False, sort=True), "Chatroulette data, current epoch")
    plotListAsHist(getFormattedList(getPokerData(allchatevents), firstElements=5, lastElements=5, groupRest=True, average=False, sort=True), "Chatpoker data, all epochs")
    plotListAsHist(getFormattedList(getPokerData(chatevents), firstElements=5, lastElements=5, groupRest=True, average=False, sort=True), "Chatpoker data, current epoch")
