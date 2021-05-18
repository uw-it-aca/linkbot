#!/usr/bin/env python3

"""Slackbot to sniff for message snippets that map to resource links.

Configuration:
    Configuration relies on a module named "linkconfig.py"
    that contains:

    #token=os.environ.get("SLACK_BOT_TOKEN")
    #signing_secret=os.environ.get("SLACK_SIGNING_SECRET"))

        1) a variable SLACK_BOT_TOKEN that holds the value for the
           Slack instance acces token
        2) a variable SLACK_SIGNING_SECRET
        3) a variable LINKBOTS that is a list of one or more dictionaries
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
from importlib import import_module
from metrics import metrics_server
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

# initialize slack API framework
slack_app = App(
    logger=logger,
    ssl_check_enabled=False,
    request_verification_enabled=False)

# import, initialize and register message event handlers for linkbots
for bot_conf in getattr(linkconfig, 'LINKBOTS', []):
    try:
        try:
            module_name = "linkbots.{}".format(bot_conf['LINK_CLASS'])
        except KeyError:
            module_name = "linkbots"

        module = import_module(module_name)
        bot = getattr(module, 'LinkBot')(bot_conf)

        logger.info("loading {}: {}".format(bot.name(), bot.match_pattern()))

        slack_app.message(bot.match_regex())(bot.send_message)

    except Exception as ex:
        raise Exception(
            "Cannot load module {}: {}".format(module_name, ex))

# prepare event endpoint
tornado_api = Application(
    [("/slack/events", SlackEventsHandler, dict(app=slack_app))])

if __name__ == '__main__':
    try:
        # open metrics exporter endpoint
        metrics_server(int(os.environ.get('METRICS_PORT', 9100)))

        # open linkbot endpoint
        tornado_api.listen(int(os.environ.get("PORT", 3000)))
        IOLoop.current().start()
    except Exception as e:
        logger.exception(e)
        logger.critical(e)
