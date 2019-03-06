#!/usr/bin/env python

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
from slacker import Slacker
from websocket import create_connection
from random import choice
import simplejson as json
import re
import sys
import linkconfig
from linkbot import clients
import logging
from logging.handlers import RotatingFileHandler
import time


logger = logging.getLogger(__name__)


class LinkBot(object):
    """Implements Slack message matching and link response

    """
    QUIPS = [
        '%s',
        'linkbot noticed a link!  %s',
        'Oh, here it is... %s',
        'Maybe this, %s, will help?',
        'Click me!  %s',
        'Click my shiny metal link!  %s',
        'Here, let me link that for you... %s',
        'Couldn\'t help but notice %s was mentioned...',
        'Not that I was eavesdropping, but did you mention %s?',
        'hmmmm, did you mean %s?',
        '%s...  Mama said there\'d be days like this...',
        '%s?  An epic, yet approachable tale...',
        '%s?  Reminds me of a story...',
    ]
    default_match = r'_THIS_COULD_BE_OVERRIDDEN_'

    def __init__(self, conf):
        self._conf = conf
        match = conf.get('MATCH', self.default_match)
        self._regex = re.compile(r'(\A|\W)+(%s)' % match, flags=re.I)
        self._quips = conf.get('QUIPS', self.QUIPS)
        self._link = conf.get('LINK', '%s|%s')
        self._quiplist = []
        self._seen = []

    def match(self, text):
        """Return a set of unique matches for text."""
        return set(match[1] for match in self._regex.findall(text))

    def message(self, link_label):
        return self._message_text(self._link % (link_label, link_label))

    def reset(self):
        self._seen = []

    def _quip(self, link):
        try:
            if not len(self._quiplist):
                self._quiplist = self._quips

            quip = choice(self._quiplist)
            self._quiplist.remove(quip)
            return quip % link
        except IndexError:
            pass

        return link

    def _message_text(self, link):
        return self._quip(link)

    def _escape_html(self, text):
        escaped = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
        }

        return "".join(escaped.get(c, c) for c in text)


class JiraLinkBot(LinkBot):
    """Subclass LinkBot to customize response for JIRA links

    """
    default_match = '[A-Z]{3,}\-[0-9]+'

    def __init__(self, conf):
        if 'LINK' not in conf:
            conf['LINK'] = '<{}/browse/%s|%s>'.format(conf['HOST'])
        super(JiraLinkBot, self).__init__(conf)
        self.jira = clients.UwSamlJira(host=conf.get('HOST'),
                                       auth=conf.get('AUTH'))

    def message(self, link_label):
        msg = super(JiraLinkBot, self).message(link_label)
        issue = self.jira.issue(link_label)
        summary = issue.fields.summary
        get_name = lambda person: person and person.displayName or 'None'
        reporter = '*Reporter* ' + get_name(issue.fields.reporter)
        assignee = '*Assignee* ' + get_name(issue.fields.assignee)
        status = '*Status* ' + issue.fields.status.name
        lines = list(map(self._escape_html,
                         [summary, reporter, assignee, status]))
        return '\n> '.join([msg] + lines)


class ServiceNowBot(LinkBot):
    _ticket_regex = '|'.join(clients.ServiceNowClient.table_map)
    default_match = '(%s)[0-9]{7,}' % _ticket_regex

    def __init__(self, conf):
        super(ServiceNowBot, self).__init__(conf)
        self.client = clients.ServiceNowClient(
            host=conf.get('HOST'), auth=conf.get('AUTH'))

    def message(self, link_label):
        record = self.client.get_number(link_label)
        link = self._strlink(link_label)
        lines = [self._quip(link)]
        for key, value in record.items(pretty_names=True):
            if key == 'Subject':
                lines.append(value or 'No subject')
            elif key == 'Parent' and value:
                link = self._strlink(value)
                lines.append('*{key}* {link}'.format(key=key, link=link))
            elif value and key != 'Number':
                lines.append('*{key}* {value}'.format(key=key, value=value))
        return '\n> '.join(lines)

    def _strlink(self, link_label):
        link = self.client.link(link_label)
        return '<{link}|{label}>'.format(link=link, label=link_label)


def configure_logging():
    format = ('%(asctime)s %(levelname)s %(module)s.'
              '%(funcName)s():%(lineno)d:'
              ' %(message)s')

    logfile = getattr(linkconfig, 'LOG_FILE', 'linkbot.log')
    if logfile == 'stdout':
        handler = logging.StreamHandler(sys.stdout)
    else:
        size = 1024 * 1024
        handler = RotatingFileHandler(
            logfile, maxBytes=size, backupCount=1)

    logging.basicConfig(level=logging.INFO, format=format, handlers=(handler,))


class SlackReceiver:
    """Slack websocket context that will try to reconnect on exception."""
    def __init__(self, client):
        self.client = client
        self.websocket = None

    def _connect(self):
        response = self.client.rtm.start()
        return create_connection(response.body['url'])

    def __enter__(self):
        logger.info('starting SlackReceiver')
        self.websocket = self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info('closing SlackReceiver')
        self.websocket.close()

    def recv(self):
        last_failure = 0
        while True:
            try:
                yield self.websocket.recv()
            except Exception as e:
                if last_failure and time.time() - last_failure < 60:
                    logger.critical('websocket failed twice in a minute')
                    raise
                logger.info('reconnecting SlackReceiver, ' + str(e))
                last_failure = time.time()
                self.websocket.close()
                self.websocket = self._connect()


def linkbot():
    """Establish Slack connection and filter messages
    
    """
    slack = Slacker(getattr(linkconfig, 'API_TOKEN'))
    robo_id = slack.auth.test().body.get('user_id')
    link_bots = []
    for bot_conf in getattr(linkconfig, 'LINKBOTS', []):
        bot_class = globals()[bot_conf.get('LINK_CLASS', 'LinkBot')]
        link_bots.append(bot_class(bot_conf))

    if not len(link_bots):
        raise Exception('No linkbots defined')

    with SlackReceiver(slack) as slack_receiver:
        for rcv in slack_receiver.recv():
            j = json.loads(rcv)

            if j.get('type') == 'message':
                if j.get('bot_id'):  # ignore all bots
                    continue

                for bot in link_bots:
                    for match in bot.match(j.get('text', '')):
                        logger.info(match + " match!")
                        try:
                            message = bot.message(match)
                        except Exception as e:
                            logger.error(e)
                            continue
                        slack.chat.post_message(
                                j.get('channel'),
                                message,
                                as_user=robo_id,
                                parse='none')


if __name__ == '__main__':
    configure_logging()
    try:
        linkbot()
    except Exception as e:
        logger.exception(e)
        logger.critical(e)
