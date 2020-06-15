FROM python:3-slim
WORKDIR /usr/src/app
RUN pip install bs4 feedparser flask gunicorn listparser lxml requests
COPY . .
EXPOSE 5000
CMD ["/usr/local/bin/gunicorn", "-b", "0.0.0.0:5000", "empocketer:app"]