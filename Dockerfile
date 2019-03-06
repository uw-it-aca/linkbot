FROM python:3.6
WORKDIR /app/
ENV PYTHONUNBUFFERED 1
ADD . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "linkbot.py"]
