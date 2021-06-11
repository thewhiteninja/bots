#! /usr/bin/env python

import datetime
import time

import irc.bot
import urllib2
from twitter import Twitter

mapSeries = {
    'dexter'   : 'dexter',
    'bbt'      : 'the-big-bang-theory',
    'ncis'     : 'ncis',
    'mentalist': 'the-mentalist',
    'howimet'  : 'how-i-met-your-mother'
}

twit = Twitter(domain="search.twitter.com")


def getTime(serie):
    p = urllib2.urlopen("http://tvcountdown.com/s/" + serie).read()
    pos = p.find("<div class=\"sixteen columns bc_f\">")
    pos = p.find("four columns", pos)
    name = p[p.find(">", pos) + 1:p.find("<", pos)]
    pos = p.find("two columns", pos)
    epi = p[p.find(">", pos) + 1:p.find("<", pos)]
    pos = p.find("href", pos)
    title = p[p.find(">", pos) + 1:p.find("<", pos)]
    pos = p.find("id", pos)
    when = p[p.find("\"", pos) + 1:p.find("\"", pos + 6)]

    stamp = p.find("var timestamp")
    stamp = p[p.find("[", stamp):p.find("]", stamp) + 1]
    stamp = eval(stamp)

    episode = p.find("var episode")
    episode = p[p.find("[", episode):p.find("]", episode) + 1]
    episode = eval(episode)

    when = stamp[episode.index(when)].replace(",", "")
    when = datetime.datetime.fromtimestamp(time.mktime(time.strptime(when, "%d %B %Y %H:%M:%S"))) + datetime.timedelta(
        hours=5)
    when = str(when - datetime.datetime.now())
    when = when[:when.rfind(".")]
    return (name, epi, title, when)


class RoxBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join('#speak')

    def on_privmsg(self, c, e):
        self.do_command(e, e.arguments()[0].strip())

    def on_pubmsg(self, c, e):
        a = e.arguments()[0]
        if len(a) > 1 and a[0] == '!':
            self.do_command(e, a[1:].strip())
        return

    def on_kick(self, c, e):
        c.join(e.target())

    def do_command(self, e, cmd):
        nick = e.source().nick
        c = self.connection
        cmds = cmd.split(" ")
        cmd = cmds[0]
        param = cmds[1] if len(cmds) > 1 else None

        if mapSeries.get(cmd) != None:
            (name, epi, title, when) = getTime(mapSeries.get(cmd))
            c.privmsg('#speak', "Next \"" + name + "\" (" + epi + ") named \"" + title + "\" in " + when)
        elif cmd == "twit" and param != None:
            results = twit.search(q=param)
            if len(results['results']) > 0:
                for i in range(min(5, len(results['results']))):
                    text = results['results'][i]['text'].strip()
                    t = time.strftime('%d/%m/%Y %H:%M:%S', time.strptime(results['results'][i]['created_at'],
                                                                         '%a %b %d %H:%M:%S +0000 %Y'))
                    textLine = ""
                    for tok in text.replace("\n", "").split(" "):
                        if len(tok) > 0 and tok[0] != "#":
                            textLine += tok + " "
                    c.privmsg('#speak', t + " - " + textLine.strip())
            else:
                c.privmsg('#speak', "No result for \"" + param + "\"")

        elif cmd == "help":
            c.privmsg('#speak', "--")
            c.privmsg('#speak', "Help")
            c.privmsg('#speak', "--")
            c.privmsg('#speak', "    Next episode : !dexter, !bbt, !ncis, !mentalist, !howimet")
            c.privmsg('#speak', "    Twitter      : !twit keyword")
            c.privmsg('#speak', "    Help         : !help")
            c.privmsg('#speak', "--")


def main():
    server = "localhost"
    port = 6667
    channel = "#speak"
    nickname = "tvbot"

    bot = RoxBot(channel, nickname, server, port)
    bot.start()


if __name__ == "__main__":
    main()
