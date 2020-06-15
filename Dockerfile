FROM python:3-slim
WORKDIR /usr/src/app
RUN pip install bs4 feedparser flask gunicorn listparser lxml requests
COPY . .
EXPOSE 5000
CMD ["/usr/local/bin/gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "300", "empocketer:app"]