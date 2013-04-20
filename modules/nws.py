#!/usr/bin/env python
'''
warnings.py -- jenni NWS Alert Module
Copyright 2011-2013, Michael Yanovich (yanovich.net)

More info:
 * jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/

This module allows one to query the National Weather Service for active
watches, warnings, and advisories that are present.
'''

import feedparser
import re
import time
import urllib
import web
import sqlite3
import string
import textwrap

states = {
        'alabama': 'al',
        'alaska': 'ak',
        'arizona': 'az',
        'arkansas': 'ar',
        'california': 'ca',
        'colorado': 'co',
        'connecticut': 'ct',
        'delaware': 'de',
        'florida': 'fl',
        'georgia': 'ga',
        'hawaii': 'hi',
        'idaho': 'id',
        'illinois': 'il',
        'indiana': 'in',
        'iowa': 'ia',
        'kansas': 'ks',
        'kentucky': 'ky',
        'louisiana': 'la',
        'maine': 'me',
        'maryland': 'md',
        'massachusetts': 'ma',
        'michigan': 'mi',
        'minnesota': 'mn',
        'mississippi': 'ms',
        'missouri': 'mo',
        'montana': 'mt',
        'nebraska': 'ne',
        'nevada': 'nv',
        'new hampshire': 'nh',
        'new jersey': 'nj',
        'new mexico': 'nm',
        'new york': 'ny',
        'north carolina': 'nc',
        'north dakota': 'nd',
        'ohio': 'oh',
        'oklahoma': 'ok',
        'oregon': 'or',
        'pennsylvania': 'pa',
        'rhode island': 'ri',
        'south carolina': 'sc',
        'south dakota': 'sd',
        'tennessee': 'tn',
        'texas': 'tx',
        'utah': 'ut',
        'vermont': 'vt',
        'virginia': 'va',
        'washington': 'wa',
        'west virginia': 'wv',
        'wisconsin': 'wi',
        'wyoming': 'wy',
}

conditions = {
    'Heat': '\x02\x0304Heat\x03\x02',
    'Flood': '\x02\x0303Flood\x03\x02',
    'Statement': '\x02\x0313__Statement__\x03\x02',
    'Surf': '\x02\x0311Surf\x03\x02',
    'Thunderstorm': '\x02\x0307Thunderstorm\x03\x02',
    'Red Flag': '\x02\x0304Red Flag\x03\x02',
    'Lake': '\x02\x0311Lake\x03\x02',
    'Effect': '\x02\x0311Effect\x03\x02',
    'Air': '\x02\x0305Air\x03\x02',
    'Tornado': '\x02\x0304!!!TORNADO!!!\x03\x02',
    'Watch': '\x02\x0308*_WATCH_*\x03\x02',
    'Warning': '\x02\x0304!WARNING!\x03\x02',
    'Severe': '\x02\x0305Severe\x03\x02',
    'Special': '\x02\x0306__Special__\x03\x02',
    'Fire': '\x02\x0304Fire\x03\x02',
    'Seas': '\x02\x0311Seas\x03\x02',
    'Danger': '\x02\x0304DANGER\x03\x02',
    'Small Craft': '\x02\x0311Small Craft\x03\x02',
    'Advisory': '\x0306Advisory\x03',
    'Hurricane': '\x02\x0313HURRICANE\x03\x02',
    'Wind': '\x02\x0311Wind\x03\x02',
    'Flash': '\x0311Flash\x03',
    'Rip Current': '\x02\x0311Rip Current\x03\x02',
    'Beach Hazards': '\x0308Beach Hazards\x03',
    'Frost': '\x02Frost\x02',
    'Quality': '\x0313Quality\x03',
    'Hydrologic': '\x0311Hydrologic\x03',
    'Weather': '\x02Weather\x02',
    'High': '\x02\x0304HIGH\x03\x02',
    'Dense Fog': '\x0303Dense Fog\x03',
    'Winter': '\x02\x0311Winter\x03\x02',
    'Rain': '\x0311Rain\x03',
    'Freezing': '\x02\x03FREEZING\x03\x02',
    'Stagnation': '\x02Stagnation\x02',
    'Freeze': '\x02\x0311FREEZE\x03\x02',
    'Chill': '\x0311Chill\x03',
    'Coastal': '\x02Coastal\x02',
    'Storm': '\x02*Storm*\x02',
    'Blizzard': '\x0311Blizzard\x03',
    'Snow': '\x0311Snow\x03',
}

county_list = 'http://alerts.weather.gov/cap/{0}.php?x=3'
alerts = 'http://alerts.weather.gov/cap/wwaatmget.php?x={0}'
zip_code_lookup = 'http://www.zip-codes.com/zip-code/{0}/zip-code-{0}.asp'
nomsg = 'There are no active watches, warnings or advisories, for {0}.'
re_fips = re.compile(r'County FIPS:</a></td><td class="info">(\S+)</td></tr>')
re_state = re.compile(r'State:</a></td><td class="info"><a href="/state/\S\S.asp">\S\S \[([A-Za-z ]+)\]</a></td></tr>')
re_city = re.compile(r'City:</a></td><td class="info"><a href="/city/\S+.asp">(.*)</a></td></tr>')
re_zip = re.compile(r'^(\d{5})\-?(\d{4})?$')
more_info = 'Complete weather watches, warnings, and advisories for {0}, available here: {1}'
warning_list = 'http://alerts.weather.gov/cap/us.php?x=1'
stop = False
CHANNEL = '##weather'
running = False


def nws_lookup(jenni, input):
    ''' Look up weather watches, warnings, and advisories. '''
    text = input.group(2)
    if not text:
        return jenni.reply('You need to provide some input.')
    bits = text.split(',')
    master_url = False
    if len(bits) == 2:
        ## county given
        url_part1 = 'http://alerts.weather.gov'
        state = bits[1].lstrip().rstrip().lower()
        county = bits[0].lstrip().rstrip().lower()
        reverse_lookup = list()
        if len(state) == 2:
            reverse_lookup = [k for k, v in states.iteritems() if v == state]
            if reverse_lookup:
                state = reverse_lookup[0]
        if state not in states and len(reverse_lookup) < 1:
            jenni.reply('State not found.')
            return
        url1 = county_list.format(states[state])
        page1 = web.get(url1).split('\n')
        prev1 = str()
        prev2 = str()
        url_part2 = str()
        for line in page1:
            mystr = '>' + unicode(county) + '<'
            if mystr in line.lower():
                url_part2 = prev2[9:40]
                break
            prev2 = prev1
            prev1 = line
        if not url_part2:
            return jenni.reply('Could not find county.')
        master_url = 'https://alerts.weather.gov/cap/' + url_part2
        location = text
    elif len(bits) == 1:
        ## zip code
        if bits[0]:
            zip_code = bits[0]
            zips = re_zip.findall(zip_code)
            if not zips:
                return jenni.reply('ZIP is invalid.')
            else:
                try:
                    zip_code = zips[0][0]
                except:
                    return jenni.reply('ZIP could not be validated.')
            urlz = zip_code_lookup.format(zip_code)
            pagez = web.get(urlz)
            fips = re_fips.findall(pagez)
            if fips:
                state = re_state.findall(pagez)
                city = re_city.findall(pagez)
                if not state and not city:
                    return jenni.reply('Could not match ZIP code to a state')
                try:
                    state = state[0].lower()
                    state = states[state].upper()
                    location = city[0] + ', ' + state
                    fips_combo = unicode(state) + 'C' + unicode(fips[0])
                    master_url = alerts.format(fips_combo)
                except:
                    return jenni.reply('Could not parse state or city from database.')
            else:
                return jenni.reply('ZIP code does not exist.')

    if not master_url:
        return jenni.reply('Invalid input. Please enter a ZIP code or a county and state pairing, such as \'Franklin, Ohio\'')

    feed = feedparser.parse(master_url)
    warnings_dict = dict()
    for item in feed.entries:
        if nomsg[:51] == item['title']:
            return jenni.reply(nomsg.format(location))
        else:
            warnings_dict[unicode(item['title'])] = unicode(item['summary'])

    if len(warnings_dict) > 0:
        if input.sender.startswith('#'):
            ## if queried in a channel
            i = 1
            for key in warnings_dict:
                if i > 1:
                    break
                jenni.reply(key)
                response = textwrap.wrap(warnings_dict[key], 450)
                resp_len = len(response)
                q = 1
                for resp in response:
                    jenni.reply('Part %s of %s: %s' % (str(q).zfill(2), str(resp_len).zfill(2), resp))
                    q += 1
                i += 1
            jenni.reply(more_info.format(location, master_url))
        else:
            ## if queried in private message
            for key in warnings_dict:
                jenni.reply(key)
                jenni.reply(warnings_dict[key])
            jenni.reply(more_info.format(location, master_url))
nws_lookup.commands = ['nws']
nws_lookup.priority = 'high'
nws_lookup.thread = True


def warns_control(jenni, input):
    global stop
    global running
    if not input.admin:
        return jenni.reply('You need to be an admin to use this!')

    if input.group(2) == 'start':
        stop = False
        if running:
            return jenni.reply('It is already running!')
        running = True
        jenni.reply('Starting...')
        weather_feed(jenni, input)
    elif input.group(2) == 'stop':
        stop = True
        if not running:
            return jenni.reply('It isn\'t running!')
        else:
            jenni.reply('Stopping...')
    else:
        response = 'NWS module is currently: '
        if running:
            jenni.reply(response + 'running')
        else:
            jenni.reply(response + 'not running')
warns_control.commands = ['warns']
warns_control.priority = 'high'
warns_control.thread = True


def weather_feed(jenni, input):
    global stop
    global running
    conn = sqlite3.connect('nws.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS nws ( area text, state text, title text )')
    conn.commit()
    c.close()

    word_re = re.compile('\w+')

    def _cap(match):
        return match.group(0).capitalize()

    def capitalize_all(s):
        return word_re.sub(_cap, s)

    if not stop:
        while True:
            if stop:
                conn.commit()
                c.close()
                stop = False
                running = False
                return jenni.reply('Checking... I\'m comleteply stopped. (stopped in "Master")')
            parsed = feedparser.parse(warning_list)
            if not len(parsed['entries']) > 0:
                continue
            for entity in parsed['entries']:
                if stop:
                    conn.commit()
                    c.close()
                    stop = False
                    running = False
                    return jenni.reply('Checking... I\'m completely stopped. (stopped inside XML Parse)')
                entry = entity
                try:
                    area = entry['cap_areadesc']
                    link = entry['link']
                    title = entry['title']
                    state = link.split('?x=')[1][:2]
                    summary = entry['summary']
                    cert = entry['cap_certainty']
                    severity = entry['cap_severity']
                    status = entry['cap_status']
                    urgency = entry['cap_urgency']
                except Exception, e:
                    jenni.msg(jenni.logchan_pm, 'No entry available. See stdout for more information.')
                    print time.time(), str(e)
                    print str(entry)
                    print ''

                ch_state = '{0}-{1}-{2}'.format(CHANNEL, 'us', state.lower())

                sql_text = (area, state, title,)
                conn = sqlite3.connect('nws.db')
                c = conn.cursor()
                c.execute('SELECT * FROM nws WHERE area = ? AND state = ? AND title = ?', sql_text)
                if len(c.fetchall()) < 1:
                    t = (area, state, title,)
                    c.execute('INSERT INTO nws VALUES (?, ?, ?)', t)
                    conn.commit()

                    for st in states:
                        if states[st] == state.lower():
                            state = st[0].upper() + st[1:]

                    for condition in conditions:
                        if condition in title:
                            title = title.replace(condition, conditions[condition])

                    state = capitalize_all(state)
                    line1 = '\x02[\x0302{1}\x03] Part {2} of {3}: {0}\x02'
                    line2 = '{0}. \x02Certainty\x02: {1}\x02, Severity\x02: {2}, \x02Status\x02: {3}, \x02Urgency\x02: {4}'
                    areas = textwrap.wrap(area, 450)
                    len_areas = len(areas)
                    counter_areas = 1
                    for each in areas:
                        jenni.msg(ch_state, line1.format(each, state, str(counter_areas).zfill(2), str(len_areas).zfill(2)))
                        counter_areas += 1
                    jenni.msg(ch_state, line2.format(title, cert, severity, status, urgency))
                    summaries = textwrap.wrap(summary, 450)
                    len_summaries = len(summaries)
                    counter_summaries = 1
                    for each in summaries:
                        jenni.msg(ch_state, 'Part %s of %s: %s' % (str(counter_summaries).zfill(2), str(len_summaries).zfill(2), each))
                        counter_summaries += 1
                conn.commit()
                c.close()
            time.sleep(60)

if __name__ == '__main__':
    print __doc__.strip()
