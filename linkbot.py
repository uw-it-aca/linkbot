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
import linkconfig
import sys
import os
import logging


# setup basic logging
logging.basicConfig(level=logging.DEBUG,
                    format=('%(asctime)s %(levelname)s %(module)s.'
                            '%(funcName)s():%(lineno)d:'
                            ' %(message)s'),
                    handlers=(logging.StreamHandler(sys.stdout),))

logger = logging.getLogger(__name__)


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
slack_app = App(
    logger=logger,
    ssl_check_enabled=False,
    request_verification_enabled=False)
    #token=os.environ.get("SLACK_BOT_TOKEN")
    #signing_secret=os.environ.get("SLACK_SIGNING_SECRET"))

# prepare metrics
linkbot_message_count = Counter(
    'message_sent_count',
    'LinkBot message match and sent count',
    ['channel'])


@slack_app.middleware
def log_request(logger, body, next):
    logger.debug("middleware log_request: {}".format(body))
    return next()


@slack_app.event("message")
def linkbot_response(event, say, logger):
    logger.debug("linbot_response: {}".format(event))
    for bot in link_bots:
        text = event.get('text', '')
        logger.debug("linkbot {}: match".format(bot.name(), text))
        for match in bot.match(text):
            logger.debug("match: {}".format(match))
            try:
                message = bot.message(match)
            except Exception as e:
                logger.error(e)
                continue

            say(message, parse='none')
            linkbot_message_count.labels(event.get('channel')).inc()


tornado_api = Application(
    [("/slack/events", SlackEventsHandler, dict(app=slack_app))])

if __name__ == '__main__':
    try:
        # open metrics exporter endpoint
        start_http_server(int(os.environ.get('METRICS_PORT', 9100)))

        # start linkbot
        tornado_api.listen(int(os.environ.get("PORT", 3000)))
        IOLoop.current().start()
    except Exception as e:
        logger.exception(e)
        logger.critical(e)
