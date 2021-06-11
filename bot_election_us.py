#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import platform
import signal
import time
from datetime import datetime
from hashlib import md5
from time import localtime

import requests
from discord_webhook import DiscordWebhook, DiscordEmbed
from lxml import html

from pypeul import *

WH_PROD = "https://discordapp.com/api/webhooks/..."

FF_HEADERS = {
    "User-Agent"   : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0",
    "DNT"          : "1",
    "Pragma"       : "no-cache",
    "Cache-Control": "no-cache",
    "TE"           : "Trailers"
}

REQUEST_URL = "https://www.theguardian.com/us-news/ng-interactive/2020/nov/03/us-election-2020-live-results-donald" \
              "-trump-joe-biden-who-won-presidential-republican-democrat"

INTERVAL = 15 * 60  # seconds
DELAY_AFTER_INIT = 60  # seconds

db = {}


def temp_filename(filename):
    prefix = md5(str(localtime()).encode('utf-8')).hexdigest()
    return f"{prefix}_{filename}"


def log(s):
    print("[+] %s" % str(s), flush=True)


def welcome():
    print("Starting %s at %s (%s version)\n" % (
        os.path.basename(sys.argv[0]), time.asctime(time.localtime(time.time())), platform.architecture()[0]),
          flush=True)


def send_to_discord(prev, last):
    webhook = DiscordWebhook(url=WH_PROD,
                             avatar_url='https://cdn.icon-icons.com/icons2/230/PNG/256'
                                        '/UnitedStates_US_USA_840_Flag3_26057.png')
    webhook.set_content("Last election results!")

    embed = DiscordEmbed(title="Biden", color=int("019BD8", 16))
    tmp = last["biden"][0]
    if last["biden"][0] != prev["biden"][0]:
        tmp += " (%s%d)" % (
            "+" if last["biden"][0] > prev["biden"][0] else "-", int(last["biden"][0]) - int(prev["biden"][0]))
    embed.add_embed_field(name=tmp, value=last["biden"][1], inline=False)
    webhook.add_embed(embed)

    embed = DiscordEmbed(title="Trump", color=int("D81C28", 16))
    tmp = last["trump"][0]
    if last["trump"][0] != prev["trump"][0]:
        tmp += " (%s%d)" % (
            "+" if last["trump"][0] > prev["trump"][0] else "-", int(last["trump"][0]) - int(prev["trump"][0]))
    embed.add_embed_field(name=tmp, value=last["trump"][1], inline=False)
    webhook.add_embed(embed)

    embed = DiscordEmbed(title="Carte par état", color=int("222222", 16))
    embed.set_url("https://www.google.com/search?q=election+usa")
    embed.set_thumbnail(url="https://www.google.com/search?q=election+usa", width=600, height=400)
    embed.set_description("https://www.google.com/search?q=election+usa")
    embed.set_timestamp()
    webhook.add_embed(embed)

    print(webhook.execute())


def tofile(t):
    f = open(temp_filename("page"), "w")
    f.write(t)
    f.close()


def fromfile(filename):
    f = open(filename, "r")
    content = f.read()
    f.close()
    return content


def scrap(url):
    s = requests.Session()
    s.headers.update(FF_HEADERS)
    r = s.get(REQUEST_URL)

    tree = html.fromstring(r.text)
    results = {
        "biden": [
            tree.xpath(
                '/html/body/div[4]/article/div/div[2]/div/figure/figure/div/div/div[1]/div/div[1]/div[1]/div[2]/div['
                '1]/div[1]/text()')[
                0].strip(),
            tree.xpath(
                '/html/body/div[4]/article/div/div[2]/div/figure/figure/div/div/div[1]/div/div[1]/div[1]/div[2]/div['
                '2]/div[2]/text()')[
                0].strip()
        ],
        "trump": [
            tree.xpath(
                '/html/body/div[4]/article/div/div[2]/div/figure/figure/div/div/div[1]/div/div[1]/div[2]/div[2]/div['
                '2]/div[2]/text()')[
                0].strip(),
            tree.xpath(
                '/html/body/div[4]/article/div/div[2]/div/figure/figure/div/div/div[1]/div/div[1]/div[2]/div[2]/div['
                '1]/div[2]/text()')[
                0].strip()
        ]
    }

    return results


def checkPosts():
    global db
    log(str(datetime.now()) + " - check")
    lastdb = scrap(REQUEST_URL)

    if lastdb["biden"][0] != db["biden"][0] or lastdb["trump"][0] != db["trump"][0]:
        send_to_discord(db, lastdb)

    db = lastdb

    thread = threading.Timer(INTERVAL, checkPosts)
    thread.start()


def initPosts():
    global db
    log("Initializing ...")
    db = scrap(REQUEST_URL)
    print(json.dumps(db, indent=4))


def runCheckThread():
    initPosts()
    thread = threading.Timer(DELAY_AFTER_INIT, checkPosts)
    thread.start()


def signal_handler(signum, frame):
    log("SIGINT received from user. Exiting ...")
    sys.exit(1)


def main():
    sys.stdout = open(os.path.basename(sys.argv[0]) + ".log", 'w')
    signal.signal(signal.SIGINT, signal_handler)
    runCheckThread()


if __name__ == "__main__":
    welcome()
    main()
