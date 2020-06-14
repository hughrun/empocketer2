FROM python:3-slim
WORKDIR /usr/src/app
RUN pip install feedparser requests
COPY . .
COPY ../settings.py .
CMD ["/usr/local/bin/python", "checker.py"]