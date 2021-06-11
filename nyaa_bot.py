#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import platform
import random
import signal
import time
import urllib.error
import urllib.parse
import urllib.request

from discord_webhook import DiscordWebhook, DiscordEmbed
from lxml import html

from pypeul import *

DL_WH = "https://discord.com/api/webhooks/..." \
        "-7R5NHlawPpPrNVzO_c5qSP4BOK9oTGlylP_"
FF_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:37.0) Gecko/20100101 Firefox/37.0"}

NYAA_URL = "https://nyaa.si/?f=0&c=1_3&q=%s"

QUERY = {
    "Edens Zero"                    : "edens+zero+1080p+vostfr",
    "Boruto"                        : "boruto+1080p+vostfr",
    "My Hero Academia"              : "my+hero+academia+1080p+vostfr",
    "One Piece"                     : "one+piece+1080p+vostfr",
    "Dragon Quest: Dai No Daibouken": "dragon+quest+dai+1080p+vostfr",
}

INTERVAL = 60  # minutes
LOG = None

db = {}


def log(s):
    global LOG
    if LOG is None:
        LOG = open("nyaabot.log", "w")
    LOG.write("[+] %s\n" % str(s))
    LOG.flush()
    print("[+] %s" % str(s), flush=True)


def welcome():
    print("Starting %s at %s (%s version)\n" % (
        os.path.basename(sys.argv[0]), time.asctime(time.localtime(time.time())), platform.architecture()[0]),
          flush=True)


def send_to_discord(name, title, url, size, seed, leech, completed):
    try:
        webhook = DiscordWebhook(url=DL_WH, username="DLBot")
        webhook.set_content("New " + str(name) + " episode!")

        embed = DiscordEmbed(title=str(title), url="https://nyaa.si" + str(url), color=242424)
        embed.set_timestamp()
        embed.add_embed_field(name='Size', value=str(size), inline=True)
        embed.add_embed_field(name='Stats', value="Seed %d/Leech %d/Completed %d" % (seed, leech, completed),
                              inline=True)

        webhook.add_embed(embed)

        webhook.execute()
    except Exception as e:
        log("Webhook failed (%s)" % str(e))


def scrap(url):
    try:
        resp = urllib.request.urlopen(urllib.request.Request(url, headers=FF_HEADERS))
        tree = html.fromstring(resp.read())

        path = '/html/body/div/div[not(contains(@class, "alert"))]/table/tbody/tr/'

        titles = tree.xpath(path + 'td[2]/a[not(@class)]/@title')
        ids = [getId(url) for url in tree.xpath(path + 'td[2]/a[not(@class)]/@href')]
        sizes = tree.xpath(path + 'td[4]/text()')
        magnets = tree.xpath(path + 'td[3]/a[1]/@href')
        seeds = list(map(int, tree.xpath(path + 'td[6]/text()')))
        leechs = list(map(int, tree.xpath(path + 'td[7]/text()')))
        completes = list(map(int, tree.xpath(path + 'td[8]/text()')))
        return ids, titles, sizes, magnets, seeds, leechs, completes

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("Exp(%s:%d) : %s" % (exc_tb.tb_frame.f_code.co_filename, exc_tb.tb_lineno, e), flush=True)


def checkPosts():
    global db

    for q in QUERY:
        log("Checking %s" % q)
        try:
            ids, titles, sizes, magnets, seeds, leechs, completes = scrap(NYAA_URL % QUERY[q])
        except Exception as e:
            log("Scaping failed: " + str(e))
            continue
        added = 0
        for i in range(len(ids)):
            if ids[i] not in db[q]:
                added += 1
                send_to_discord(q, titles[i], magnets[i], sizes[i], seeds[i], leechs[i], completes[i])
                db[q].add(ids[i])
        log("%d items added" % added)
        time.sleep(random.randrange(10, 30))
    thread = threading.Timer(INTERVAL * 60.0, checkPosts)
    thread.start()


def getId(s):
    n = ""
    for c in s[6:]:
        if c in "0123456789":
            n += c
        else:
            break
    return int(n)


def initPosts():
    global db
    log("Initializing posts...")
    for q in QUERY:
        ids, titles, sizes, magnets, seeds, leechs, completes = scrap(NYAA_URL % QUERY[q])
        db[q] = set()
        for i in range(len(ids)):
            db[q].add(ids[i])
        log("%d item(s) loaded for %s" % (len(db[q]), q))
        time.sleep(random.randrange(10, 20))
    log("Initialization done.")


def runCheckThread():
    initPosts()
    thread = threading.Timer(10.0, checkPosts)
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
