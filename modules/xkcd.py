#!/usr/bin/env python
"""
xkcd.py - XKCD Module
Copyright 2010-2013 Michael Yanovich (yanovich.net), and Morgan Goose
Licensed under the Eiffel Forum License 2.

More info:
 * jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

from lxml import etree
import random
import web


random.seed()


def xkcd(jenni, input):
    """.xkcd - Generates a url for a random XKCD clip."""

    page = web.get("https://xkcd.com/rss.xml")
    body = page.split("\n")[1]
    parsed = etree.fromstring(body)
    newest = etree.tostring(parsed.findall("channel/item/link")[0])
    max_int = int(newest.split("/")[-3])
    website = "https://xkcd.com/%d/" % random.randint(0, max_int + 1)
    jenni.say(website)
xkcd.commands = ['xkcd']
xkcd.priority = 'low'
xkcd.rate = 10

if __name__ == '__main__':
    print __doc__.strip()
