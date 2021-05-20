#!/usr/bin/env python3
# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0
"""Slackbot to sniff for message snippets that map to resource links.

Configuration:
    Configuration relies on a module named "linkconfig.py"
    in the same directory as linkbot.py containing definitions for:

    SLACK_BOT_TOKEN - Slack instance auth
    SLACK_SIGNING_SECRET - Slack intance auth
    LINKBOTS - array of dictionaries defining links to report, containing
        MATCH - regex used to match message link cues
        LINK - link format used to report match
      or
        LINK_CLASS - linkbots.LinkBot subclass
        plus other keys necessary to support class configuration

Run linkbot

    1) Setup a .env file for docker defining the various config

    2) $ docker-compose up --build
"""

from slack_bolt import App
from importlib import import_module
from util.slash_cmd import SlashCommand
from util.metrics import metrics_server
from util.endpoint import init_endpoint_server, endpoint_server
import linkconfig
import sys
import os
import logging


# setup basic logging
logging.basicConfig(level=logging.INFO,
                    format=('%(asctime)s %(levelname)s %(module)s.'
                            '%(funcName)s():%(lineno)d:'
                            ' %(message)s'),
                    handlers=(logging.StreamHandler(sys.stdout),))

logger = logging.getLogger(__name__)

# initialize slack API framework
slack_app = App(
    logger=logger,
    ssl_check_enabled=False)

# import, initialize and register message event handlers for linkbots
bot_list = []
for bot_conf in getattr(linkconfig, 'LINKBOTS', []):
    try:
        try:
            module_name = "linkbots.{}".format(bot_conf['LINK_CLASS'])
        except KeyError:
            module_name = "linkbots"

        module = import_module(module_name)
        bot = getattr(module, 'LinkBot')(bot_conf)
        bot_list.append(bot)

        logger.info("loading {}: {}".format(bot.name(), bot.match_pattern()))

        # add bot's message event handler
        slack_app.message(bot.match_regex())(bot.send_message)

    except Exception as ex:
        logger.error(
            "Cannot load module {}: {}".format(module_name, ex))

if len(bot_list) < 1:
    logger.error("No linkbots configured")


@slack_app.middleware
def message_filter(payload, logger, next):
    if payload.get('bot_id') is None:
        next()

    logger.debug('filtered bot message')

# prepare linkbot slash command
slash_cmd = SlashCommand(bot_list=bot_list, logger=logger)
slack_app.command("/{}".format(slash_cmd.name))(slash_cmd.command)

# prepare slack event endpoint
init_endpoint_server(slack_app)

if __name__ == '__main__':
    try:
        # open metrics exporter endpoint
        metrics_server(int(os.environ.get('METRICS_PORT', 9100)))

        # open slack event endpoint
        endpoint_server(int(os.environ.get("PORT", 3000)))
    except Exception as e:
        logger.exception(e)
        logger.critical(e)
