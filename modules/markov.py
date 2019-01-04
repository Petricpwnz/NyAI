import json
import codecs
import random
import traceback


MINCHAINLENGTH = 4
MAXCHAINLENGTH = 20
CHAINLENGTHCHANCE = 0.92


class Markov():
    def __init__(self, plugin, wordfilepath):
        self.plugin = plugin
        self.wordfilepath = wordfilepath
        self.markovwords = {}
        try:
            with open(self.wordfilepath, 'r+') as file:
                self.markovwords = json.load(file)
        except Exception:
            print(traceback.format_exc())
            pass

    def getInfo(self):
        return "[path: " + self.wordfilepath + ", count: " + str(len(self.markovwords)) + "]"

    def save(self, path=False):
        if not path:
            path = self.wordfilepath
        with open(path, 'w+') as file:
            json.dump(self.markovwords, file, indent=2)
            file.close()

    def addFile(self, filename, filetype="LOG"):
        '''
        Add content of a file to the markov words
        '''
        file = codecs.open(filename, encoding='utf-8')
        if filetype == "LOG":
            for line in file:
                linesplit = line.replace("\n", "").split("> ", maxsplit=1)
                if len(linesplit) < 2:
                    continue
                self.addLine(linesplit[1])
        elif filetype == "RAW":
            for line in file:
                line.replace("\n", "")
                self.addLine(line)
        file.close()

    def addLine(self, line):
        if line.startswith("!"):
            return
        words = line.replace('\n', '').replace('\r', '').replace('\t', '').split()
        if len(words) < 2:
            return
        # forwards chain probs
        for i in range(0, len(words) - 1):
            wg = self.markovwords.get(words[i], self.__getMarkovWordsTemplate())
            wg['wordsF'][words[i + 1]] = wg['wordsF'].get(words[i + 1], 0) + 1
            wg['usesF'] = wg['usesF'] + 1
            self.markovwords[words[i]] = wg
        # backwards chain probs
        for i in range(1, len(words)):
            wg = self.markovwords.get(words[i], self.__getMarkovWordsTemplate())
            wg['wordsB'][words[i - 1]] = wg['wordsB'].get(words[i - 1], 0) + 1
            wg['usesB'] = wg['usesB'] + 1
            self.markovwords[words[i]] = wg
        # start / uses / end counter
        wg = self.markovwords.get(words[-1], self.__getMarkovWordsTemplate())
        wg['end'] = wg['end'] + 1
        wg['usesF'] = wg['usesF'] + 1
        self.markovwords[words[-1]] = wg
        wg = self.markovwords.get(words[0], self.__getMarkovWordsTemplate())
        wg['start'] = wg['start'] + 1
        wg['usesB'] = wg['usesB'] + 1
        self.markovwords[words[0]] = wg

    def __getMarkovWordsTemplate(self):
        return {'end': 0, 'usesF': 0, 'wordsF': {},
                'start': 0, 'usesB': 0, 'wordsB': {}}

    def pickRandomStartWord(self):
        keys = self.markovwords.keys()
        word = False
        for i in range(1000):
            word = random.sample(keys, 1)[0]
            wordgroup = self.markovwords[word]
            if random.random() < (wordgroup.get("start", 0) / wordgroup.get("usesF", 1)):
                return word
        return word

    def forwardSentence(self, word, length, targetChannel, includeWord=False):
        if not word:
            word = self.pickRandomStartWord()
        sentence = ""
        if includeWord:
            sentence += word
        for i in range(0, length):
            wordGroup = self.markovwords.get(word, False)
            if self.__decideToStartEnd(self.__endSentenceWithWordProb(wordGroup), i, length):
                break
            if wordGroup and len(wordGroup['wordsF']) > 0:
                word, stop = False, True
                for _ in range(10):
                    word, _ = self.plugin.pickWeightedRandom(wordGroup['wordsF'])
                    if self.__isSuitableChainWord(word, targetChannel):
                        stop = False
                        break
                if stop:
                    break
                sentence += " " + word
            else:
                break
        return sentence

    def backwardSentence(self, word, length, targetChannel, includeWord=False):
        sentence = ""
        if includeWord:
            sentence += word
        for i in range(0, length):
            wordGroup = self.markovwords.get(word, False)
            if self.__decideToStartEnd(self.__startSentenceWithWordProb(wordGroup), i, length):
                break
            if wordGroup and len(wordGroup['wordsB']) > 0:
                word, stop = False, True
                for _ in range(10):
                    word, _ = self.plugin.pickWeightedRandom(wordGroup['wordsB'])
                    if self.__isSuitableChainWord(word, targetChannel):
                        stop = False
                        break
                if stop:
                    break
                sentence = word + " " + sentence
            else:
                break
        return sentence

    def chainprob(self, word1, word2=False):
        if not word2:
            wordGroup = self.markovwords.get(word1, self.__getMarkovWordsTemplate())
            return 'Probabilities: start sentence {start}, end sentence {end}'.format(**{
                   "start": format(self.__startSentenceWithWordProb(wordGroup), '.4f'),
                   "end": format(self.__endSentenceWithWordProb(wordGroup), '.4f'),
            })
        else:
            wordGroupF = self.markovwords.get(word1, self.__getMarkovWordsTemplate())
            totalf = wordGroupF['usesF']
            countf = wordGroupF['wordsF'].get(word2, 0)
            wordGroupB = self.markovwords.get(word2, self.__getMarkovWordsTemplate())
            totalb = wordGroupB['usesB']
            countb = wordGroupB['wordsB'].get(word1, 0)
            if (totalf <= 0):
                return 'Word ' + word1 + " has never been used."
            if (totalb <= 0):
                return 'Word ' + word1 + " has never been used."
            return 'Probabilities: forward {countf}/{totalf}, backward {countb}/{totalb}'.format(**{
                "countf": countf,
                "totalf": totalf,
                "pf": countf / totalf,
                "countb": countb,
                "totalb": totalb,
                "pb": countb / totalb,
            })
        return ""

    def __decideToStartEnd(self, p, i, maxi):
        if i < MINCHAINLENGTH:
            return False
        return random.random() < (p * (1 + i / maxi))

    def __startSentenceWithWordProb(self, wordGroup):
        if wordGroup:
            return max([0, (wordGroup.get('start', 0) / max([wordGroup.get('usesB', 0), 1])) - 0.02])
        return 1

    def __endSentenceWithWordProb(self, wordGroup):
        if wordGroup:
            return max([0, (wordGroup.get('end', 0) / max([wordGroup.get('usesF', 0), 1])) - 0.02])
        return 1

    def __isSuitableChainWord(self, word, channel):
        if self.plugin.isInChannel(word, channel):
            return False
        if "http://" in word or "https://" in word:
            return False
        if self.markovwords.get(word, {}).get('disabled', False):
            return False
        return True

    def chainLength(self):
        for i in range(MINCHAINLENGTH, MAXCHAINLENGTH):
            if random.random() > CHAINLENGTHCHANCE:
                return i
        return MAXCHAINLENGTH

    def getWord(self, word):
        return self.markovwords.get(word)

    def delWord(self, word):
        # does not prevent the word from appearing at start/end of a sentence, only to chain further
        if self.markovwords.get(word):
            del self.markovwords[word]
            return True
        return False

    def disableWord(self, word):
        wordGroup = self.markovwords.get(word, False)
        wordGroup['disabled'] = True
