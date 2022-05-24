FROM python:3.8
ENV LOG_FILE stdout
WORKDIR /app/
ENV PYTHONUNBUFFERED 1
ADD . /app
WORKDIR /app
RUN pip install -r requirements.txt
RUN cp linkconfig_example.py linkconfig.py
RUN groupadd -r linkbot && useradd -r -g linkbot linkbot
RUN chgrp -R linkbot . && chmod -R g=u .
USER linkbot
CMD ["python", "linkbot.py"]
