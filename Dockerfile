FROM python:3-alpine
WORKDIR /usr/src/app
RUN pip install bs4 feedparser flask gunicorn listparser requests
COPY . .
EXPOSE 5000
CMD ["/usr/local/bin/gunicorn", "-b", "0.0.0.0:5000", "empocketer:app"]