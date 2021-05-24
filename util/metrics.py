# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0
"""
Functions supporting Prometheus metrics
"""
from prometheus_client import start_http_server, Counter

# prepare metrics
linkbot_message_count = Counter(
    'message_sent_count',
    'LinkBot message match and sent count',
    ['channel'])


def metrics_counter(channel_name):
    """ Increment channel_name message counter
    """
    linkbot_message_count.labels(channel_name).inc()


def metrics_server(port):
    """ Serve metrics requests
    """
    start_http_server(port)
