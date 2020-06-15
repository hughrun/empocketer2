#!/usr/local/bin/python3

# copied from Alex Mill's script at https://gist.github.com/alexmill/9bc634240531d81c3abe
from bs4 import BeautifulSoup as bs4
import requests
import feedparser
import socket
import urllib.parse

socket.setdefaulttimeout(60) # set a socket timeout for feedparser

def findfeed(site):
    raw = requests.get(site, allow_redirects=True, timeout=60).text
    result = []
    possible_feeds = []
    html = bs4(raw, features="lxml")
    feed_urls = html.findAll("link", rel="alternate")
    if len(feed_urls) > 1:
        for f in feed_urls:
            t = f.get("type",None)
            if t:
                if "rss" in t or "xml" in t:
                    href = f.get("href",None)
                    if href:
                        possible_feeds.append(href)
    parsed_url = urllib.parse.urlparse(site)
    base = parsed_url.scheme+"://"+parsed_url.hostname
    atags = html.findAll("a")
    for a in atags:
        href = a.get("href",None)
        if href:
            if "xml" in href or "rss" in href or "feed" in href:
                possible_feeds.append(base+href)
    for url in list(set(possible_feeds)):
        f = feedparser.parse(url)
        if len(f.entries) > 0:
            if url not in result:
                result.append(url)
    return(result)