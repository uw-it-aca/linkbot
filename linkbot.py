#!/usr/bin/env python3

"""Slackbot to sniff for message snippets that map to resource links.

Configuration:
    Configuration relies on a module named "linkconfig.py"
    that contains:

        1) a module variable API_TOKEN that holds the value for the
           Slack instance acces token
        2) a variable LINKBOTS that is a list of one or more dictionaries
           defining:
            a) MATCH key that is a string within messages to match
            b) LINK that is a slack format link definition

Run linkbot

        $ python linkbot.py
"""

from slack_bolt import App
from slack_bolt.adapter.tornado import SlackEventsHandler
from tornado.web import Application
from tornado.ioloop import IOLoop
from prometheus_client import start_http_server, Counter
from importlib import import_module
import sys
import os
import linkconfig
import logging
from logging.handlers import RotatingFileHandler


logger = logging.getLogger(__name__)


def configure_logging():
    format = ('%(asctime)s %(levelname)s %(module)s.'
              '%(funcName)s():%(lineno)d:'
              ' %(message)s')

    logfile = getattr(linkconfig, 'LOG_FILE')
    if not logfile or logfile == 'stdout':
        handler = logging.StreamHandler(sys.stdout)
    else:
        size = 1024 * 1024
        handler = RotatingFileHandler(
            logfile, maxBytes=size, backupCount=1)

    logging.basicConfig(level=logging.DEBUG,
                        format=format, handlers=(handler,))


# import and initialize linkbot responders
link_bots = []
for bot_conf in getattr(linkconfig, 'LINKBOTS', []):
    try:
        try:
            module_name = "linkbots.{}".format(bot_conf['LINK_CLASS'])
        except KeyError:
            module_name = "linkbots"

        print("loading {}".format(module_name))
        logger.info("loading {}".format(module_name))

        module = import_module(module_name)
        link_bots.append(getattr(module, 'LinkBot')(bot_conf))
    except Exception as ex:
        raise Exception(
            "Cannot load module {}: {}".format(module_name, ex))

if not len(link_bots):
    raise Exception('No linkbots defined')

# initialize slack
slack_app = App()
#    token=os.environ.get("SLACK_BOT_TOKEN"),
#    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
#)

# prepare metrics
linkbot_message_count = Counter(
    'message_sent_count',
    'LinkBot message match and sent count',
    ['channel'])


@slack_app.middleware
def log_request(logger, body, next):
    logger.debug(body)
    return next()


@slack_app.event("message")
def linkbot_response(body, say, logger):
    logger.debug("message event: {}".format(body))
    for bot in link_bots:
        for match in bot.match(body.get('text', '')):
            logger.info(match + " match!")
            try:
                message = bot.message(match)
            except Exception as e:
                logger.error(e)
                continue

            say(message, parse='none')
            linkbot_message_count.labels(body.get('channel')).inc()


api = Application([("/slack/events", SlackEventsHandler, dict(app=slack_app))])

if __name__ == '__main__':
    configure_logging()

    try:
        # open metrics exporter endpoint
        start_http_server(int(os.environ.get('METRICS_PORT', 9100)))

        # start linkbot
        api.listen(int(os.environ.get("PORT", 3000)))
        IOLoop.current().start()
    except Exception as e:
        logger.exception(e)
        logger.critical(e)
