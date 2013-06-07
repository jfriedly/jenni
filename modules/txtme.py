#!/usr/bin/env python
"""
txtme.py - jenni's SMS Notifications Module
Copyright 2013 - Joel Friedly
Licensed under the Eiffel Forum License 2.

More info:
 * jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/

This module detects your nick and texts you when you're mentioned in chat
but inactive.
"""
import os
import time
from modules import gcsms
try:
    from ConfigParser \
        import SafeConfigParser, NoSectionError, NoOptionError
except ImportError:
    from configparser \
        import SafeConfigParser, NoSectionError, NoOptionError


last_active = time.time()


def say_it(jenni, input):
    global last_active
    if input.nick == jenni.config.owner:
        last_active = time.time()
    elif jenni.config.owner in input:
        if time.time() - last_active > jenni.config.activity_timeout:
            cfg = SafeConfigParser()
            cfg.read(os.path.expanduser('~/.gcsms'))
            txt = "[{0}] {1}: {2}".format(input.sender, input.nick, input)
            gcsms.cmd_send(cfg, text=txt)
say_it.rule = r'(.*)'
say_it.priority = "high"
say_it.rate = 20


if __name__ == '__main__':
    print __doc__
