#!/usr/bin/env python
"""
twss.py - Jenni's That's What She Said Module
Copyright 2011 - Joel Friedly and Matt Meinwald

Licensed under the Eiffel Forum License 2.

This module detects common phrases that many times can be responded with
"That's what she said."

It also allows users to add new "that's what she said" jokes to it's library 
by following any appropriate statement with ".twss".
"""

import urllib2, re, os, sys, pickle


last = "DEBUG_ME" # if you see this in the terminal, something broke.

if not os.path.exists("modules/twss.txt"):
    f = open("modules/twss.txt", "w")
    url = "http://www.twssstories.com/best?page="
    first_re = re.compile(r"<p>.+TWSS\.*</p>")
    inner_re = re.compile(r'".+"')
    url2 = "http://www.shesaidit.ca/index.php?pageno="
    second_re = re.compile(r'"style30">.*</span>')

    print "Now creating TWSS database. This will take a few minutes.",
    for page in range(1,148):
        sys.stdout.flush()
        print ".",
        curr_url = url + str(page)
        html = urllib2.urlopen(curr_url)
        story_list = first_re.findall(html.read())
        for story in story_list:
            if len(inner_re.findall(story)) > 0:
                lowercase =  inner_re.findall(story)[0].lower()
                f.write(re.sub("[^\w\s]", "", lowercase) + "\n")

    for page in range(1,157):
        sys.stdout.flush()
        print ".",
        curr_url = url2 + str(page)
        html = urllib2.urlopen(curr_url)
        matches_list = second_re.findall(html.read())
        for match in matches_list:
             lowercase = match[10:-7].lower().strip()
             if len(inner_re.findall(lowercase)) > 0:
                 lowercase = inner_re.findall(lowercase)[0]
             f.write(re.sub("[^\w\s]", "", lowercase) + "\n")
    f.close()


def ls_prob(count, total, classes=2.0, k=1.0):
    """ Returns the Laplacian Smoothed probability of a word appearing. """
    return (count + k) / (total + float(classes))


def twss_prob(quote, twss, not_twss, total_dict_size, twss_num_words, not_twss_num_words, twss_jokes, not_twss_jokes):
    """ Returns the estimated probability that a given quote can be responded to with TWSS. """
    top = ls_prob(twss_jokes, twss_jokes+not_twss_jokes)
    bottom = ls_prob(not_twss_jokes, twss_jokes+not_twss_jokes)
    for word in quote.split(" "):
        top *= ls_prob((twss[word] if word in twss else 0), twss_num_words, total_dict_size)
        bottom *= ls_prob((not_twss[word] if word in not_twss else 0), not_twss_num_words, total_dict_size)
    bottom += top
    print top / bottom
    return top / bottom


def analyze_words(filename):
    """ Returns a 'bag of words' representation of all the words in the file.  That is, a dictionary containing word counts for every word. """
    f = open(filename, "r")
    lines = 0
    words = {}
    num_words = 0
    for line in f:
        for word in line.split(" "):
            if word in words:
                words[word] += 1
            else:
                words[word] = 1
            num_words += 1
        lines += 1
    return (words, num_words, lines)


def combine_dicts(dict1, dict2):
    """ Returns the length of the set of all unique keys in two dictionaries. """
    everything = set(dict1.keys())
    everything.update(dict2.keys())
    return len(everything)


def say_it(jenni, input):
    """ Master function that calls everything else and says TWSS iff it's a joke. """
    global last
   # user_quotes = None
   # if os.path.exists("modules/twss_user_added.txt"):
   #     with open("modules/twss_user_added.txt") as f2:
   #         user_quotes = frozenset([line.rstrip() for line in f2])
    formatted = input.group(0).lower()
    twss, twss_num_words, twss_jokes = analyze_words("modules/twss.txt")
    not_twss, not_twss_num_words, not_twss_jokes  = analyze_words("modules/not_twss.txt")
    total_dict_size = combine_dicts(twss, not_twss)
    if twss_prob(formatted, twss, not_twss, total_dict_size, twss_num_words, not_twss_num_words, twss_jokes, not_twss_jokes) > .9925:
        jenni.say("That's what she said.")
    last = re.sub("[^\w\s]", "", formatted) 
say_it.rule = r".*"
say_it.priority = "high"


#def add_twss(jenni, input):
#    print last
#    with open("modules/twss_user_added.txt", "a") as f:
#        f.write(re.sub(r"[^\w\s]", "", last.lower()) + "\n")
#        f.close()
#    jenni.say("That's what she said.")
#add_twss.commands = ["twss"]
#add_twss.priority = "low"


if __name__ == '__main__':
    print __doc__.strip()
