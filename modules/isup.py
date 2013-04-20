#!/usr/bin/env python
"""
isup.py - Simple website status check with isup.me
Copyright 2013, Michael Yanovich (yanovich.net)
Copyright 2012, 2013 Edward Powell (embolalaia.net)
Licensed under the Eiffel Forum License 2.

This allows users to check if a website is up through isup.me.

More info:
 * Willie: http://willie.dftba.net/
 * jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

import re
import web

def isup(jenni, input):
    """isup.me website status checker"""
    site = input.group(2)
    if not site:
        return jenni.reply("What site do you want to check?")

    if site[:6] != 'http://' and site[:7] != 'https://':
        if '://' in site:
            protocol = site.split('://')[0] + '://'
            return jenni.reply("Try it again without the %s" % protocol)
        else:
            site = 'http://' + site
    try:
        response = web.get(site)
    except Exception as e:
        jenni.say(site + ' looks down from here.')
        return

    if response:
        jenni.say(site + ' looks fine to me.')
    else:
        jenni.say(site + ' is down from here.')
isup.commands = ['isup']
isup.example = ".isup google.com"

if __name__ == '__main__':
    print __doc__.strip()
