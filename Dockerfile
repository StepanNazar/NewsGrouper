FROM python:3.12-slim

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY src/news_grouper/api news_grouper/api
COPY migrations migrations

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "news_grouper.api.prod:app"]