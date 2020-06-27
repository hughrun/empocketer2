import datetime, feedparser, json, requests, sched, settings, sqlite3, time

# ===============================================================
# here's the function to check all the feeds every X hours
# ===============================================================

def check_feeds():

    db = sqlite3.connect('data/empocketer.db')
    cursor = db.cursor()
    cursor.execute('SELECT DISTINCT url, last_published_float, user_token, id FROM feeds')
    feeds = cursor.fetchall()
    db.close()
    for feed in feeds:
        data = feedparser.parse(feed[0])
        for post in data.entries:
            if ( 'published_parsed' in post and time.mktime(post.published_parsed) > feed[1]):

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
                          "access_token": feed[2]
                      })

                  r = requests.post(url, data=payload, headers=headers)

                  if r.status_code == 200:
                      # update the last_published_float value for this feed listing only
                      # if we update all feeds with this URL, we might update one that 
                      # hasn't been processed yet.
                      db = sqlite3.connect('data/empocketer.db')
                      cursor = db.cursor()
                      t = (time.mktime(post.published_parsed),feed[3],) 
                      cursor.execute('UPDATE feeds SET last_published_float=? WHERE id=?', t)
                      db.commit()
                      db.close()
              except Exception as e:
                print('ERROR', datetime.datetime.now(), str(e))

    schedule_run()

# Schedule checking feeds every minute 
def schedule_run():
    s = sched.scheduler(time.time, time.sleep)
    frequency = 60 * 60 * settings.frequency
    s.enter(frequency, 1, check_feeds)
    s.run()

# kick off
schedule_run()
