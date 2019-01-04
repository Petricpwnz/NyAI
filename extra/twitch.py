import threading
import socket
import time
import re
# import random


class twitchThread(threading.Thread):
    def __init__(self, bot, plugin, markov):
        threading.Thread.__init__(self)
        self.daemon = True
        self.bot = bot
        self.plugin = plugin
        self.channels = {}
        self.markov = markov
        self.sock = socket.socket()
        self.sock.connect((self.bot.config['twitchhost'], self.bot.config['twitchport']))
        self.sock.send("PASS {}\r\n".format(self.bot.config['twitchoauth']).encode("utf-8"))
        self.sock.send("NICK {}\r\n".format(self.bot.config['twitchnick']).encode("utf-8"))
        self.keepRunning = True

    def run(self):
        while self.keepRunning:
            response = self.sock.recv(1024).decode("utf-8")
            if response == "PING :tmi.twitch.tv\r\n":
                print('[twitch] ping-pong')
                self.sock.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
            else:
                username = re.search(r"\w+", response).group(0)  # return the entire match
                restsplit = response.split(" PRIVMSG ")
                if len(restsplit) < 2:
                    continue
                restsplit = (restsplit[1]).split(" :")
                if len(restsplit) < 2:
                    continue
                channel = restsplit[0]
                message = restsplit[1]
                message = message.replace("\r", "").replace("\n", "")
                print('[twitch] ' + channel + ': <' + username + '> ' + message)
                if message.startswith("!"):
                    args = (message).split(" ")
                    if args[0] == "!chain":
                        self.commandChain(username, channel, args)
                    elif args[0] == "!chainf":
                        self.commandChainf(username, channel, args)
                    elif args[0] == "!chainb":
                        self.commandChainb(username, channel, args)
            time.sleep(0.1)

    def stop(self):
        self.keepRunning = False

    def join(self, channel):
        self.sock.send("JOIN {}\r\n".format(channel).encode("utf-8"))
        self.channels[channel] = 1
        print('[twitch] joined ' + channel)

    def leave(self, channel):
        self.sock.send("PART {}\r\n".format(channel).encode("utf-8"))
        self.channels[channel] = 0
        if sum(self.channels.values()) < 1:
            self.stop()
        print('[twitch] left ' + channel)

    def message(self, channel, msg):
        s = "PRIVMSG {channel} :{msg}".format(**{
            "channel": channel,
            "msg": msg + "\r\n",
        })
        self.sock.send(s.encode("utf-8"))

    def timeout(self, channel, name, secs=600):
        self.message(channel, ".timeout {}".format(name, secs))

    def commandChain(self, nick, channel, args):
        if len(args) < 2:
            return
        if self.plugin.spam_protect('twitchchain', nick, channel, {}, specialSpamProtect='twitchchain', ircSpamProtect=False):
            return
        word = args[1]
        forward = self.markov.forwardSentence(word, 20, channel, includeWord=False)
        backward = self.markov.backwardSentence(word, 20, channel, includeWord=True)
        s = backward + forward
        self.message(channel, s)

    def commandChainf(self, nick, channel, args):
        if len(args) < 2:
            return
        if self.plugin.spam_protect('twitchchain', nick, channel, {}, specialSpamProtect='twitchchain', ircSpamProtect=False):
            return
        word = args[1]
        s = self.markov.forwardSentence(word, 10, channel, includeWord=True)
        self.message(channel, s)

    def commandChainb(self, nick, channel, args):
        if len(args) < 2:
            return
        if self.plugin.spam_protect('twitchchain', nick, channel, {}, specialSpamProtect='twitchchain', ircSpamProtect=False):
            return
        word = args[1]
        s = self.markov.backwardSentence(word, 10, channel, includeWord=True)
        self.message(channel, s)
