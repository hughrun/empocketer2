import datetime, feedparser, json, requests, settings, sqlite3, time

# ===============================================================
# here's the function to check all the feeds every X period of time
# ===============================================================

def check_feeds():

    try:
        db = sqlite3.connect('data/empocketer.db')
        cursor = db.cursor()
        cursor.execute('SELECT DISTINCT url, last_published_float, list_id, id FROM feeds')
        feeds = cursor.fetchall()
        db.close()
    except Exception as e:
        print('ERROR connecting to DB ', datetime.datetime.now(), str(e))

    for feed in feeds:
        data = feedparser.parse(feed[0])
        lpf = feed[1]
        new_published = None
        db = sqlite3.connect('data/empocketer.db')
        c = db.cursor()
        c.execute('SELECT token FROM users INNER JOIN lists ON lists.owner_username = users.username WHERE lists.id = ' + str(feed[2]))
        token = c.fetchone()[0]
        db.close()

        for post in data.entries:
            if ( 'published_parsed' in post and time.mktime(post.published_parsed) > lpf):

              try:
                  url = 'https://getpocket.com/v3/add'
                  
                  headers = {
                      'content-type' : 'application/json; charset=UTF-8',
                      'X-Accept' : 'application/json'
                      }
                  
                  payload = json.dumps({
                          "url": post.link,
                          "tags": "empocketer",
                          "consumer_key": settings.consumer_key,
                          "access_token": token
                      })

                  r = requests.post(url, data=payload, headers=headers)
                  if r.status_code == 200:
                      if time.mktime(post.published_parsed) > lpf:
                          if new_published and time.mktime(post.published_parsed) > new_published:
                              new_published = post.published_parsed

                  else:
                      print(datetime.datetime.now(), ' - Pocket API error for ', post.link)
                      print(r.text)

              except Exception as e:
                print('ERROR contacting Pocket', datetime.datetime.now(), str(e))

        if new_published:
            # Update last published value
            # We do this AFTER running through all articles in case there are multiple posts since the last run
            db = sqlite3.connect('data/empocketer.db')
            cursor = db.cursor()
            published = time.strftime('%a %d %b %Y', new_published)
            t = (published, time.mktime(new_published),feed[3],) 
            cursor.execute('UPDATE feeds SET last_published=?, last_published_float=? WHERE id=?', t)
            db.commit()
            db.close()

# trigger
check_feeds()