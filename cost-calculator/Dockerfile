FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY requirements.txt .
COPY server server

EXPOSE 5000

ENTRYPOINT ["/usr/local/bin/gunicorn", "-k", "gevent", "-w", "4", "-b", ":5000", "--access-logfile", "-", "--error-logfile", "-", "server:app"]
