# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0
"""
Helper functions
"""

channel_cache = {'None': 'None'}


def channel_name(channel_id, client):
    """ Given a channel id, return corresponding channel name
    """
    channel = str(channel_id)
    if channel not in channel_cache:
        try:
            info = client.conversations_info(channel=channel_id)
            channel_cache[channel] = info['channel']['name']
        except Exception:
            channel_cache[channel] = channel_id

    return channel_cache[channel]
