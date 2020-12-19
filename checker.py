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
                      # update the last_published and last_published_float values for this feed listing, but only if the published date is newer than the most recent post recorded.

                      # Note that we don't rely on the value we got from the database because if the feed is arranged in reverse-chronological order we will end up recording a date that is the least-recent post in the feed instead of the most-recent.
                    
                    if time.mktime(post.published_parsed) > lpf:

                        db = sqlite3.connect('data/empocketer.db')
                        cursor = db.cursor()
                        published = time.strftime('%a %d %b %Y', post.published_parsed)
                        t = (published, time.mktime(post.published_parsed),feed[3],) 
                        cursor.execute('UPDATE feeds SET last_published=?, last_published_float=? WHERE id=?', t)
                        db.commit()
                        db.close()

                        # update lpf value for the rest of this loop
                        lpf = time.mktime(post.published_parsed)

              except Exception as e:
                print('ERROR', datetime.datetime.now(), str(e))
# trigger
check_feeds()