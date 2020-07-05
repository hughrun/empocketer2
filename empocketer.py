#!/usr/bin/env python3

#    empocketer version 2 : an RSS-to-Pocket web app
#    Copyright (C) 2020  Hugh Rundle
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

from collections import namedtuple
import feedparser
from feedfinder import findfeed
from flask import Flask, abort, make_response, redirect, render_template, request, Response, session, url_for
import json
import listparser as lp
from random import randint
import re
import requests
import socket
import settings
import sqlite3
import time

socket.setdefaulttimeout(60) # set a socket timeout for feedparser

# ===============================================================
# Create sqlite database if it does not already exist
# ===============================================================

db = sqlite3.connect('data/empocketer.db')

cursor = db.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY NOT NULL, 
        username TEXT NOT NULL UNIQUE, 
        token TEXT NOT NULL)
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS lists(
        id INTEGER PRIMARY KEY NOT NULL, 
        name TEXT NOT NULL, 
        owner_username TEXT NOT NULL, 
        UNIQUE(name, owner_username)
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS feeds(
        id INTEGER PRIMARY KEY NOT NULL,
        link TEXT NOT NULL,
        url TEXT NOT NULL,
        name TEXT NOT NULL,
        image TEXT NOT NULL, 
        last_published TEXT, 
        last_published_float REAL,
        failing INTEGER NOT NULL, 
        list_id INTEGER NOT NULL,
        user_token TEXT NOT NULL,
        UNIQUE(url, list_id)
    )
''')

db.commit()
db.close()

# ===============================================================
# Functions
# ===============================================================

def user_owns_list(list_id):

    if 'username' in session:
        # get data from database
        db = sqlite3.connect('data/empocketer.db')
        cursor = db.cursor()
        t = (list_id,)
        cursor.execute('''
                SELECT owner_username FROM lists
                WHERE lists.id=?''', t)
        user_data = cursor.fetchone()
        db.close()
        if user_data:
            if user_data[0] == session["username"]:
                return True
            else:
                return False
        else:
            abort(400) # bad request (id wasn't provided or doesn't exist)
    else:
        abort(401)

def user_owns_feed(feed_id):

    if 'username' in session:
        # get data from database
        db = sqlite3.connect('data/empocketer.db')
        cursor = db.cursor()
        t = (feed_id,)
        cursor.execute('''
                SELECT user_token FROM feeds
                WHERE feeds.id=?''', t)
        feed_data = cursor.fetchone()
        if feed_data:
            # does this token belong to the logged in user?
            u = (session['username'],)
            cursor.execute('''
                SELECT token FROM users
                WHERE users.username=?''', u)
            list_data = cursor.fetchone()
            db.close()
            if list_data[0] == feed_data[0]:
                return True
            else:
                return False
        else:
            db.close()
            abort(400) # bad request (id wasn't provided or doesn't exist)
    else:
        abort(401)


def add_feed_to_db(args):
    try:
        if 'url' in args:
            # get feed link from site
            feed = findfeed(args['url'])

            if feed == None:
                return {
                    "status" : "error",
                    "error" : "URL has no feed or does not exist"
                }
        else:
            feed = args['feed']

        data = feedparser.parse(feed)

        if data.bozo:

            not_feed = str(data.bozo_exception)[:9] == '<unknown>'

            if not_feed:
                return {
                    "status" : "error",
                    "error" : "URL has no feed or does not exist"
                }

        x = randint(1, 20)
        image_location = '../static/images/feeds/' + str(x) + '.jpg'

        if 'updated' in data.feed:
            date_stamp = data.feed.updated_parsed
            published = time.strftime('%a %d %b %Y', date_stamp)
        elif 'published' in data.feed:
            date_stamp = data.feed.published_parsed
            published = time.strftime('%a %d %b %Y', date_stamp)
        elif len(data.entries) > 0 and 'published_parsed' in data.entries[0]:
            i = len(data.entries) - 1
            first_date_stamp = data.entries[0].published_parsed
            last_date_stamp = data.entries[i].published_parsed
            is_reverse_chron = time.mktime(first_date_stamp) > time.mktime(last_date_stamp)
            date_stamp = first_date_stamp if is_reverse_chron else last_date_stamp
            published = time.strftime('%a %d %b %Y', date_stamp)
        elif 'modified' in data:
            date_stamp = data.modified_parsed
            published = time.strftime('%a %d %b %Y', date_stamp)
        else:
            date_stamp = time.localtime(time.time())
            published = 'unknown'
        
        pf = time.mktime(date_stamp)
        
        if 'link' in data.feed:
            feed_link = data.feed.link

        if 'title' in data.feed and len(data.feed.title) > 0:
            feed_title = data.feed.title[:60]
        elif 'link' in data.feed and len(data.feed.link) > 0:
            feed_title = data.feed.link[:60]
        elif 'url' in args:
            feed_url = args['url']
            feed_title = feed_url[:60]
        else:
            feed_url = args['feed']
            feed_title = feed_url[:60]

        # pass an error back if the feed can't be parsed
        # connect to database
        db = sqlite3.connect('data/empocketer.db')
        cursor = db.cursor()
        u = (session['username'],)
        cursor.execute('SELECT token FROM users WHERE username=?', u)
        user_token = cursor.fetchone()
        f = (feed_title, feed, feed_link, image_location, published, pf, 0, args['list_id'], user_token[0],)
        cursor.execute('INSERT INTO feeds(name, url, link, image, last_published, last_published_float, failing, list_id, user_token) VALUES(?,?,?,?,?,?,?,?,?)', f)
        db.commit()
        feed_id = cursor.lastrowid
        db.close()
        payload = {
            "status" : "active",
            "feed_id" : feed_id,
            "image" : image_location,
            "latest" : published,
            "name" : feed_title,
            "url" : feed,
            "link" : feed_link 
        }

        return {
            "status" : "ok",
            "feed" : payload,
            "error" : None
        }
    except Exception as e:
        
        unique = str(e)[:6] == "UNIQUE"

        if unique:
            
            return {
                "status" : "error",
                "error" : "Feed is already in this list!"
            }
        
        else:

            return {
                "status" : "error",
                "error" : "Could not read feed - " + str(e)
            }

# ===============================================================
# Routes with Flask
# ===============================================================

app = Flask(__name__)
app.secret_key = 'alkd8034nc*)_)(^asdaj;j'

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    else:
        resp = make_response(render_template('index.html'))
        return resp

@app.route('/login/')
def login():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    else:
        try:
            # POST to Pocket to get an authorisation code
            headers = {
                'content-type' : 'application/json; charset=UTF-8',
                'X-Accept' : 'application/json'
                }
            redirect_uri = settings.url + "/authorise"
            url = 'https://getpocket.com/v3/oauth/request'
            payload = json.dumps(
                {
                    "consumer_key": settings.consumer_key,
                    "redirect_uri": redirect_uri
                }
            )
            r = requests.post(url, data=payload, headers=headers, timeout=20)

            # now redirect the user to Pocket, with the code
            data = r.json()
            authorize_url = 'https://getpocket.com/auth/authorize?request_token=' + data['code'] + '&redirect_uri=' + redirect_uri
            # store the code in the session data because we need it later at /authorise
            session['auth_code'] = data['code']
            return redirect(authorize_url, code=307)
        except Exception as e:
            print(e)
            abort(500)

@app.route('/authorise/')
def authorise():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    elif 'auth_code' in session:
        # send login details to Pocket then redirect to dashboard
        headers = {
            'content-type' : 'application/json; charset=UTF-8',
            'X-Accept' : 'application/json'
            }
        url = 'https://getpocket.com/v3/oauth/authorize'
        payload = json.dumps(
            {
                "consumer_key" : settings.consumer_key,
                "code" : session['auth_code']
            }
        )
        r = requests.post(url, data=payload, headers=headers,timeout=20)
        data = r.json()
        # add or update user in database
        db = sqlite3.connect('data/empocketer.db')
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO users(username, token) VALUES(?,?)
            ON CONFLICT(username) DO UPDATE SET token=excluded.token
            ''',
            (data['username'], data['access_token'])
        )
        db.commit()
        db.close()
        # now that we've logged in we no longer need the auth code
        session.pop('auth_code', None)
        # set session username
        session['username'] = data['username']
        # now redirect to dashboard
        return redirect(url_for('dashboard'), code=307)
    else:
        return redirect(url_for('index'), code=307)

@app.route('/me/')
def dashboard():
    if 'username' in session:
        resp = make_response(render_template('dashboard.html'))
        return resp
    else:
        return redirect(url_for('index'))

@app.route('/logout/')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

# delete-account
@app.route('/delete-user') 
def delete_user():
    # check is logged in
    if 'username' in session:

        try:
            db = sqlite3.connect('data/empocketer.db')
            cursor = db.cursor()
            u = (session['username'],)
            cursor.execute('SELECT token FROM users WHERE username=?', u)
            user_token = cursor.fetchone()[0]
            t = (user_token,)
            # remove feeds
            cursor.execute('DELETE FROM feeds WHERE feeds.user_token=?', t)
            db.commit()
            # remove lists
            cursor.execute('DELETE FROM lists WHERE lists.owner_username=?', u)
            db.commit()
            # remove user
            cursor.execute('DELETE FROM users WHERE users.username=?', u)
            db.commit()
            db.close()
            # log out the session
            session.pop('username', None)
            # redirect
            return redirect(url_for('delete_account'))
        except Exception:
            abort(500)
    else:
        abort(401)

@app.route('/deleted-account/')
def delete_account():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    else:
        resp = make_response(render_template('deleted-account.html'))
        return resp

# ===============================================================
# json POST routes for Vue
# ===============================================================

@app.route('/user-details')
def user_details():
    if 'username' in session:
        # get data from database
        db = sqlite3.connect('data/empocketer.db')
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        t = (session['username'],)
        cursor.execute('''
                SELECT feeds.id AS feedid, lists.id AS listid, lists.name AS listname, feeds.name AS feedname, feeds.url AS url, feeds.link as link, feeds.image AS image, feeds.last_published AS latest, feeds.failing AS status FROM lists
                LEFT JOIN feeds ON lists.id = feeds.list_id
                WHERE lists.owner_username=?''', t)
        user_data = cursor.fetchall()
        db.close()

        # We do a bit of gymnastics with our results here because we want to
        # get the feeds into a List for each 'list' they are in.
        # That is, we have a list of tuples but need a nested dict
        # collections.namedtuple to the rescue...

        UserLists = namedtuple('UserLists', 'feedid, listid, listname, feedname, url, link, image, latest, status')

        lists = {}
        obj = { 
            "username" : session['username'],
            "lists" : [] 
            }

        for entry in map(UserLists._make, user_data):

            if entry.status:
                status_class = 'failing'
            else:
                status_class = 'active'

            addition = {
                "feed_id" : entry.feedid, 
                "name" : entry.feedname, 
                "url" : entry.url, 
                "link" : entry.link, 
                "latest" : entry.latest, 
                "image" : entry.image, 
                "status" : status_class
                }

            # construct a dict for each list of feeds
            if entry.listid in lists:
                lists[entry.listid]['feeds'].append(addition)
            else:
                lists[entry.listid] = {"name" : entry.listname, "list_id" : entry.listid, "feeds" : []}
                if entry.url:
                    lists[entry.listid]['feeds'].append(addition)

        # now push each of those dicts into a list of lists
        for k in lists.keys():
            obj['lists'].append(lists[k])

        if user_data:
            return obj
        else:
            return {
                "username" : session['username'],
                "lists" : []
            }
    else:
        abort(401)

@app.route('/add-list', methods=['POST']) 
def add_list():
    if 'username' in session:
        try:
            # get data from database
            db = sqlite3.connect('data/empocketer.db')
            cursor = db.cursor()
            req_data = request.get_json()
            l = (req_data['list_name'], session['username'],) 
            cursor.execute('INSERT INTO lists(name, owner_username) VALUES(?,?)', l)
            db.commit()
            list_id = cursor.lastrowid
            db.close()
            # return JSON
            return {
                "status" : "ok",
                "list_id" : list_id,
                "error" : None
            }
        except sqlite3.IntegrityError as e:
            print(str(e))
            db.close()
            if str(e)[:8] == "NOT NULL":
               return {
                "status" : "error",
                "error" : "List name must be provided"
               }
            elif str(e)[:6] == "UNIQUE":
                return {
                    "status" : "error",
                    "error" : "List name must be unique"
                }
            else:
                return {
                    "status" : "error",
                    "error" : str(e)
                }
        except Exception as e:
            db.close()
            return {
                "status" : "error",
                "error" : str(e)
            }
    else:
        abort(401)

@app.route('/add-feed', methods=['POST'])
def add_feed():

    if 'username' in session:
        req_data = request.get_json()
        return add_feed_to_db(req_data)
        
    else:
        abort(401)

@app.route('/upload-opml', methods=['POST'])
def upload_opml():
    if 'username' in session:
        try:
            urls = []
            f = request.files['file']
            # parse opml file
            outline = lp.parse(f)
            for site in outline.feeds:
                urls.append({"url": site.url, "category" : site.categories[0][0]})
            # return a JSON list of feed URLs
            return {
                "status" : "ok",
                "feeds" : urls
            }
        except Exception as e:
            return {
                "status" : "error",
                "error" : str(e)
            }

    else:
        abort(401)

@app.route('/add-from-opml', methods=['POST'])
def add_from_opml():
    if 'username' in session:
        try:
            req_data = request.get_json()
            # check if there is a list name the same as category
            category = req_data['category']
            url = req_data['feed']
            db = sqlite3.connect('data/empocketer.db')
            cursor = db.cursor()
            c = (category,)
            cursor.execute('SELECT id FROM lists WHERE name=?', c)
            list_id = cursor.fetchone()
            if list_id and len(list_id) > 0:
                # if yes, use that list id and add the feed
                args = {
                    "feed" : url,
                    "list_id" : list_id[0]
                }

                return_value = add_feed_to_db(args)

                # return with status ok
                return return_value

            else:
                # if no, add a new list with that name, then add the feed with the new list id

                l = (category, session['username'],) 
                cursor.execute('INSERT INTO lists(name, owner_username) VALUES(?,?)', l)
                db.commit()

                args = {
                    "feed" : url,
                    "list_id" : cursor.lastrowid
                }

                return_value = add_feed_to_db(args)
                # return with status ok
                return return_value

        except Exception as e:
            print(e)
            return {
                "status" : "error",
                "error" : str(e)
            }
    else:
        abort(401)

@app.route('/rename-list', methods=['POST']) 
def rename_list():
    if 'username' in session:
        try:
            req_data = request.get_json()
            list_id = req_data['list_id'] 
            permitted = user_owns_list(list_id)
            # Check whether the list belongs to this user
            if permitted:
                db = sqlite3.connect('data/empocketer.db')
                cursor = db.cursor()
                l = (req_data['list_name'], req_data['list_id'],) 
                cursor.execute('UPDATE lists SET name=? WHERE id=?', l)
                db.commit()
                db.close()
                # return JSON
                return {
                    "status" : "ok",
                    "error" : None
                }
            else:
                abort(403)

        except Exception as e:
            if str(e)[:10] == "'NoneType'":
                return {
                    "status" : "error",
                    "error" : "Valid list name and id must be provided"
                }
            else:
                return {
                    "status" : "error",
                    "error" : str(e)
                }
    else:
        abort(401)

@app.route('/rename-feed', methods=['POST']) 
def rename_feed():
    if 'username' in session:
        try:
            req_data = request.get_json()
            feed_id = req_data['feed_id'] 
            permitted = user_owns_feed(feed_id)
            # Check whether the list belongs to this user
            if permitted:
                db = sqlite3.connect('data/empocketer.db')
                cursor = db.cursor()
                f = (req_data['feed_name'], feed_id,) 
                cursor.execute('UPDATE feeds SET name=? WHERE id=?', f)
                db.commit()
                db.close()
                # return JSON
                return {
                    "status" : "ok",
                    "error" : None
                }
            else:
                abort(403)

        except Exception as e:
            if str(e)[:10] == "'NoneType'":
                return {
                    "status" : "error",
                    "error" : "Valid feed name and id must be provided"
                }
            else:
                return {
                    "status" : "error",
                    "error" : str(e)
                }
    else:
        abort(401)

# delete-feed
@app.route('/delete-feed', methods=['POST'])
def delete_feed():
    # check is logged in
    if 'username' in session:

        # check user owns the feed
        req_data = request.get_json()
        feed_id = req_data['feed_id'] 
        permitted = user_owns_feed(feed_id)
        f = (feed_id,)
        if permitted:
            try:
                # remove from feeds
                db = sqlite3.connect('data/empocketer.db')
                cursor = db.cursor()
                cursor.execute('DELETE FROM feeds WHERE feeds.id=?', f)
                db.commit()
                db.close()
                # return JSON
                return {
                    "status" : "ok",
                    "error" : None
                }
            except Exception as e:
                db.close()
                return {
                    "status" : "error",
                    "error" : str(e)
                }
        else:
            abort(403)
    else:
        abort(401)

# delete-list
@app.route('/delete-list', methods=['POST']) 
def delete_list():
    # check is logged in
    if 'username' in session:
        # check user owns the list
        req_data = request.get_json()
        list_id = req_data['list_id']
        permitted = user_owns_list(list_id)
        i = (list_id,)
        if permitted:
            try:
                db = sqlite3.connect('data/empocketer.db')
                cursor = db.cursor()
                # remove all feeds
                cursor.execute('DELETE FROM feeds WHERE feeds.list_id=?', i)
                db.commit()
                # remove from lists
                cursor.execute('DELETE FROM lists WHERE lists.id=?', i)
                db.commit()
                db.close()
                # return JSON
                return {
                    "status" : "ok",
                    "error" : None
                }
            except Exception as e:
                db.close()
                return {
                    "status" : "error",
                    "error" : str(e)
                }
        else:
            abort(403)
    else:
        abort(401)