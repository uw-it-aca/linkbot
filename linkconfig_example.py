# Copyright 2022 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

# LinkBot Configuration

import os
from ast import literal_eval

SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
SLACK_SIGNING_SECRET = os.environ.get('SLACK_SIGNING_SECRET')
LOG_FILE = os.environ.get('LOG_FILE', 'linkbot.log')
JIRA_HOST = os.environ.get('JIRA_HOST')
UW_SAML_CREDENTIALS = os.environ.get('UW_SAML_CREDENTIALS')
SERVICE_NOW_HOST = os.environ.get('SERVICE_NOW_HOST')
SERVICE_NOW_CREDENTIALS = os.environ.get('SERVICE_NOW_CREDENTIALS')


LINKBOTS = []


if SERVICE_NOW_HOST and SERVICE_NOW_CREDENTIALS:
    LINKBOTS.append({
        'LINK_CLASS': 'servicenowbot',
        'HOST': SERVICE_NOW_HOST,
        'AUTH': literal_eval(SERVICE_NOW_CREDENTIALS)
    })

if JIRA_HOST:
    if UW_SAML_CREDENTIALS:
        LINKBOTS.append({
            'LINK_CLASS': 'jirabot',
            'HOST': JIRA_HOST,
            'AUTH': literal_eval(UW_SAML_CREDENTIALS)
        })
    else:
        LINKBOTS += [
            {
                'MATCH': 'req[0-9]+',
                'LINK': '<{}/u_simple_requests.do?sysparm_type=labels'
                '&sysparm_table=u_simple_requests'
                '&sysparm_query=number=%s|%s>'.format(JIRA_HOST)
            },
            {
                'MATCH': 'inc[0-9]+',
                'LINK': '<{}/incident.do?sys_id=%s|%s>'.format(JIRA_HOST)
            },
            {
                'MATCH': '[Kk][Bb][0-9]+',
                'LINK': '<{}/nav_to.do?uri=/kb_view.do?'
                'sysparm_article=%s|%s>'.format(JIRA_HOST),
            },
        ]
