#!/usr/bin/env python3

# based on Alex Mill's script at https://gist.github.com/alexmill/9bc634240531d81c3abe
from bs4 import BeautifulSoup as bs4
import feedparser
import re
import requests
import socket
import urllib.parse

socket.setdefaulttimeout(60) # set a socket timeout for feedparser

def findfeed(site):
    headers = {
        'User-Agent': 'empocketer/2.0 (https://github.com/hughrun/empocketer2)'
    } # some servers require a User-Agent otherwise they respond with a 403 status
    raw = requests.get(site, headers=headers, allow_redirects=True, timeout=60).text
    first_result = []
    possible_feeds = []
    html = bs4(raw, features="lxml")
    feed_urls = html.findAll("link", rel="alternate")
    parsed_url = urllib.parse.urlparse(site)
    base = parsed_url.scheme+"://"+parsed_url.hostname
    if len(feed_urls) > 0:
        for f in feed_urls:
            t = f.get("type",None)
            if t:
                if "rss" in t or "xml" in t:
                    href = f.get("href",None)
                    if href:
                        if bool(urllib.parse.urlparse(href).netloc): # check for relative URLs
                            possible_feeds.append(href)
                        else:
                            possible_feeds.append(base+href)
    atags = html.findAll("a")
    for a in atags:
        href = a.get("href",None)
        if href:
            if "xml" in href or "rss" in href or "feed" in href:
                if bool(urllib.parse.urlparse(href).netloc): # check for relative URLs
                    possible_feeds.append(href)
                else:
                    possible_feeds.append(base+href)
    for url in list(set(possible_feeds)):
        f = feedparser.parse(url)
        if len(f.entries) > 0 and f.status == 200: # don't use redirects
            if url not in first_result:
                first_result.append(url)

    if len(first_result) > 1:
        result = []
        for url in first_result:
            possible_comments = re.search('comments', url) # remove comments feed
            if not possible_comments:
                result.append(url)
        if len(result) == 0:
            result = first_result # if we now have no feeds, use the original result
        
    else:
        result = first_result # if there was only one feed in the first place just use that
    
    response = result[0] if len(result) > 0 else None
    return(response)