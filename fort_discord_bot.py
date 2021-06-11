#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import platform
import signal
import time
import urllib.error
import urllib.parse
import urllib.request

from discord_webhook import DiscordWebhook, DiscordEmbed
from lxml import html

from pypeul import *

DISCORD_WH = "https://discordapp.com/api/webhooks/..."
FF_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:37.0) Gecko/20100101 Firefox/37.0"}

WEBSITE = "..."

INTERVAL = 10  # minutes

db = []


def log(s):
    print("[+] %s" % str(s), flush=True)


def welcome():
    print("Starting %s at %s (%s version)\n" % (
        os.path.basename(sys.argv[0]), time.asctime(time.localtime(time.time())), platform.architecture()[0]),
          flush=True)


def send_to_discord(username, url, description, replies, tag):
    webhook = DiscordWebhook(url=DISCORD_WH, username="FortBot")

    embed = DiscordEmbed(title=tag, description=description, color=242424)
    embed.set_author(name=username)
    embed.set_timestamp()
    embed.add_embed_field(name='Lien', value=url)
    embed.add_embed_field(name='Réponses', value=replies)

    img = getImageFromPost(url)
    if img is not None:
        embed.set_image(url=img)

    webhook.add_embed(embed)

    print(webhook.execute())


def getImageFromPost(url):
    try:
        resp = urllib.request.urlopen(urllib.request.Request(url, headers=FF_HEADERS))
        tree = html.fromstring(resp.read())
        pics = [i.strip() for i in tree.xpath('//img[@class="postimage"]/@src')]
        if len(pics) > 0:
            return filter2(pics[0])
        return None
    except Exception as e:
        print(e)


def scrap(url):
    try:
        resp = urllib.request.urlopen(urllib.request.Request(url, headers=FF_HEADERS))
        tree = html.fromstring(resp.read())
        topics = [i.text_content() for i in tree.xpath('//div[@class="forumbg"]//a[@class="topictitle"]')]

        tags = []
        filtered_topics = []
        for topic in topics:
            cat = None
            for word in topic.lower().split():
                if "vente" in word or "€" in word:
                    cat = "Vente"
                    break
                if word in ["don", "[don]", "donne", "[donne]", "gratuit", "[gratuit]"] or "[don]" in word:
                    cat = "Don"
                    break
                if word in ["recherche", "perdu", "demande", "cherche"]:
                    cat = "Recherche"
                if cat is None:
                    cat = "Vente"
            tags.append(cat)
            filtered_topics.append(filter_topics(topic))

        links = [filter2(i) for i in tree.xpath('//div[@class="forumbg"]//a[@class="topictitle"]/@href')]
        ids = [getId(i) for i in tree.xpath('//div[@class="forumbg"]//a[@class="topictitle"]/@href')]
        usernames = list(
            enumerate([i.strip() for i in tree.xpath('//div[@class="forumbg"]//a[@class="username"]/text()')[1:]]))
        usernames = [value for counter, value in usernames if counter % 3 == 1]
        replies = [int(i.strip()) for i in tree.xpath('//div[@class="forumbg"]//dd[@class="posts"]/text()')[1:]]

        return ids, filtered_topics, replies, links, usernames, tags
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("Exp(%s:%d) : %s" % (exc_tb.tb_frame.f_code.co_filename, exc_tb.tb_lineno, e), flush=True)
        return None, None, None, None, None, None


def checkPosts():
    global db
    log("check")
    try:
        ids, topics, replies, links, usernames, tags = scrap("https://" + WEBSITE + "/forum/viewforum.php?f=38")
        if ids is not None:
            knownIds = [i[0] for i in db]
            for i in zip(ids, topics, replies, links, usernames, tags):
                if i[0] not in knownIds and i[5] is not None and i[2] == 0:
                    log("new" + json.dumps(i, indent=4))
                    send_to_discord(username=i[4], url=i[3], description=i[1], replies=i[2], tag=i[5])
                    db.insert(0, i)
        thread = threading.Timer(INTERVAL * 60.0, checkPosts)
        thread.start()
    except urllib.error.URLError as e:
        log("urlerror - " + str(e))
    except Exception as e:
        log("error - " + str(e))


def filter_topics(s):
    s = s.lower().strip()
    for toremove in ["[donne]", "[don]", "[vente]", "(vente)", "(donne)", "donne", "vente", "don", "[]"]:
        s = s.replace(toremove, "")
    return s.strip().capitalize()


def filter2(s):
    s = s.replace("./", "https://" + WEBSITE + "/forum/")
    return s.strip()


def getId(s):
    start = s.find("t=") + 2
    end = s.find("&", start)
    return int(s[start:end])


def initPosts():
    global db
    log("Initializing posts ...")
    ids, topics, replies, links, usernames, tags = scrap("https://" + WEBSITE + "/forum/viewforum.php?f=38")
    print(ids)
    print(topics)
    print(replies)
    print(links)
    print(usernames)
    print(tags)
    for i in zip(ids, topics, replies, links, usernames, tags):
        db.append(i)
    log("%d post(s) loaded" % len(topics))


def runCheckThread():
    initPosts()
    thread = threading.Timer(8.0, checkPosts)
    thread.start()


def signal_handler(signum, frame):
    log("SIGINT received from user. Exiting ...")
    sys.exit(1)


def main():
    signal.signal(signal.SIGINT, signal_handler)
    runCheckThread()


if __name__ == "__main__":
    welcome()
    main()
