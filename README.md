## About

Empocketer allows you to subscribe to RSS feeds and pipe new content directly into your Pocket account. You can use the site URL, feed URL, or an OPML file to add feeds, and use lists to keep them organised.

See it in action at [demo.empocketer.hugh.run](https://demo.empocketer.hugh.run)

### Credits

Login page photo by [Katarina Šikuljak](https://unsplash.com/@neko_tamo?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText) on Unsplash. 

Default feed images from [Biodiversity Heritage Library](https://www.biodiversitylibrary.org). 

Fonts used are [Jr Hand](https://www.fontsquirrel.com/fonts/Jr-Hand),[ASAP Medium](https://www.fontsquirrel.com/fonts/asap) and Tahoma.

This app uses [Flask](https://flask.palletsprojects.com/en/1.1.x/), [Vue](https://vuejs.org/), [axios](https://www.npmjs.com/package/axios), [Python feedparser](https://pythonhosted.org/feedparser/index.html), [sqlite](https://sqlite.org/index.html), [gunicorn](https://gunicorn.org/), [Docker Compose](https://docs.docker.com/compose/), and [Alex Mill's 'feedfinder' script](https://gist.github.com/alexmill/9bc634240531d81c3abe). Thanks to everyone involved in all those projects.

## Installation

1. clone the repository
2. copy settings-example.py to settings.py
3. paste in your app `consumer_key` and your app's `url` into settings.py, and if necessary adjust the `frequency` (in hours) that the checker function runs (default is 2 hours)
4. set up a reverse-proxy (nginx recommended) to route localhost port 5000 to your app's URL
5. `docker-compose up --build -d`
6. consider setting up a firewall to block external access to port 5000 if you haven't done so already

## Contributing & reporting bugs

Contributions welcome - please log an issue.

## License

[AGPL 3+](LICENSE)