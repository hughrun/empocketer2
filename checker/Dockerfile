FROM python:3-alpine
WORKDIR /usr/src/app
RUN pip install feedparser requests
COPY checker/checker.py .
ADD settings.py .
CMD ["/usr/local/bin/python", "checker.py"]