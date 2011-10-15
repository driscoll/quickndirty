#!/usr/bin/python
"""
Quick and dirty Twitter search tool

Typical use:

$ python searchtwitter.py "#occupykingslanding" "#ows" >> occupyla.csv

Sample output:

"123857240330481664","RT @RolandSlinger: I'm tired of King Joffrey and his Lannister 1%! #OccupyKingsLanding","1318364841","rwggomes","155117397","None","&lt;a href=&quot;https://chrome.google.com/extensions/detail/encaiiljifbdbjlphpgpiimidegddhic&quot; rel=&quot;nofollow&quot;&gt;Silver Bird&lt;/a&gt;","None","en","http://a0.twimg.com/profile_images/1458581430/novo_penteado_normal.jpg"

Copyright 2011 Kevin Driscoll <driscollkevin@gmail.com>
This version was released under an MIT License.

TODO
* verbose option to output some info to console 
* commandline options for since, until
* need to beef up the piping

"""

import json
import optparse
import urllib2
from datetime import date, datetime
from urllib import urlencode
from sys import exit 
from time import strptime, sleep
from calendar import timegm

TWIT_DATETIME_FORMAT = '%a, %d %b %Y %H:%M:%S +0000'
 
API = u'http://search.twitter.com/search.json'
USER_AGENT = u'Quick N Dirty Search'

VERBOSE = False 

# Ordered list of tweet dict keys 
# to structure CSV output 
CSV_COLUMNS = [
    'id_str',
    'text',
    'created_at', # saved as UNIX epoch
    'from_user',
    'from_user_id_str',
    'to_user_id_str',
    'source',
    'geo',
    'iso_language_code',
    'profile_image_url'
]
CSV_DELIMITER = u','
CSV_QUOTECHAR = u'"'
CSV_REPLACE_QUOTE= u'&quot;'
CSV_LINETERMINATOR = u'\n'
CSV_ESCAPECHAR = u'\\'
SLEEP = 10

def _request(params):
    """Query API with params, parse JSON results
    Returns results as dict"""
    request = urllib2.Request(url = API)
    request.add_header('User-Agent', USER_AGENT)
    # params need to be encoded in UTF-8
    # before getting passed to urlencode
    request.add_data(urlencode(params))
    r = None 
    while not r: 
        try:
            r = urllib2.urlopen(request) 
        except urllib2.HTTPError, err:
            if (err.code == '403') or (err.code == '420'):
                log('Probably hit the rate limit.')
                r = None
                zzz()
                log('Awake!')
            else:
                # TODO make this smarter
                log("Undefined HTMLError...")
                log(err.code)
                exit(1)
        except urllib2.URLError, err:
            # TODO make this smarter
            log("Undefined URLError...")
            log(err.args)
            exit(1)
    results = json.load(r)
    return results 

def search(q, since_id=1, until='', maxpages=15):
    """Query search.twitter.com for str q

        q        : (str) e.g. u'#civicpaths'
        since_id : (int) earliest ID to search from
            if undefined, you may max out. 
        until   : (str) 'YYYY-MM-DD'

    Returns list of tweets"""
    # YYYY-MM-DD format documented here:
    # https://dev.twitter.com/docs/api/1/get/search
    if not until:
        until = date.today().strftime('%Y-%m-%d')

    # 15 is hardcoded here based on vague
    # upper limit of "roughly 1500" results
    # https://dev.twitter.com/docs/api/1/get/search/
    if (maxpages > 15) or (maxpages < 1):
        maxpages = 15

    # Search API search method documentation
    #   https://dev.twitter.com/docs/api/1/get/search
    params = {
        'q' : q,
        'page' : '1',
        'result_type' : 'recent',
        'rpp' : '100',
        'until' : until,
        'since_id' : since_id,
        'include_entities' : '1',
        'with_twitter_user_id' : '1'
    }
  
    # TODO params should be utf-8 before they get sent 
    response = _request(params)
 
    tweets = []
    tweets += response[u'results']
    while (u'next_page' in response.keys()) and (response[u'page'] < maxpages):
        # Here we're using the params returned by the Search API
        # we might consider parsing and constructing our own
        params = urllib2.urlparse.parse_qs(response[u'next_page'].lstrip('?'))
        for p in params.keys():
            params[p] = params[p][0]
        response = _request(params)
        tweets += response[u'results']
    return tweets 

def tweet_to_csv(tweet):
    """Format a tweet (dict) as CSV
    """
    # Note: Unicode console print fails sometimes
    # See: http://wiki.python.org/moin/PrintFails
    csv = u''
    for col in CSV_COLUMNS:
        csv += CSV_QUOTECHAR
        if (col == u'created_at'):
            csv += unicode(timegm(strptime(tweet[u'created_at'], TWIT_DATETIME_FORMAT)))
        elif (col == u'text'):
            # TODO UnicodeEncodeError
            csv += unicode(tweet[col].replace(CSV_QUOTECHAR, CSV_REPLACE_QUOTE))
        else:
            csv += unicode(tweet[col])
        csv += CSV_QUOTECHAR + CSV_DELIMITER 
    csv = csv[:-1] + CSV_LINETERMINATOR
    return csv 

def zzz(sec=SLEEP):
    """Sleep for a semi-random number of sec
    """
    nap = sec * datetime.now().second
    log('Taking nap for {0}s...'.format(nap))
    sleep(nap)

def log(s):
    """If VERBOSE is True, print s to console
    """
    if VERBOSE:
        print s.encode('utf-8')

def typical(keywords):
    output = ''
    for kw in keywords:
        log('Searching for {0}...'.format(kw).encode('utf-8'))
        results = search(kw)
        log('Found {0} tweets.'.format(len(results)))
        for tweet in results:
            output += tweet_to_csv(tweet)
    return output[:-1]

if __name__=='__main__':
    # First deal with options 
    p = optparse.OptionParser(
            description=' Search Twitter and return results as CSV on stdout',
            prog='searchtwitter',
            version='searchtwitter 0.1',
            usage=' python %prog.py "KEYWORD"...')
    # TODO Verbose option temporarily removed because typical
    # use is to pipe all output into a file
    # p.add_option('-v', '--verbose', action ='store_true', help='returns verbose output')
    options, arguments = p.parse_args() 
    if len(arguments) < 1:
        p.print_help()
    else:
        # if options.verbose:
        #    VERBOSE = True
 
        keywords = list(arguments)

        # Next, run the typical process
        output = typical(keywords)

        # Finally, print output to console
        print output.encode('utf-8')

