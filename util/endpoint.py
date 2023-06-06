# Copyright 2023 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

# Copyright 2022 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0
"""
Functions providing linkbot events endpoint
"""

from slack_bolt.adapter.tornado import SlackEventsHandler
from tornado.web import Application
from tornado.ioloop import IOLoop

tornado_api = None


# prepare slack event endpoint
def init_endpoint_server(slack_app):
    global tornado_api

    tornado_api = Application(
        [("/slack/events", SlackEventsHandler, {'app': slack_app})])


# run slack event endpoing
def endpoint_server(port):
    tornado_api.listen(port)
    IOLoop.current().start()
