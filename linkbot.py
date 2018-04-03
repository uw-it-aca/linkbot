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
import linkconfig
from linkbot import saml


class LinkBotSeenException(Exception): pass


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

    def __init__(self, conf):
        self._conf = conf
        self._match = conf.get('MATCH')
        self._quips = conf.get('QUIPS', self.QUIPS)
        self._link = conf.get('LINK', '%s|%s')
        self._quiplist = []
        self._seen = []

    def match(self, text):
        return re.findall(r'(\A|\W)(%s)(\W|\Z)' % self._match, text, flags=re.I)

    def message(self, link_label):
        if link_label in self._seen:
            raise LinkBotSeenException(link_label)

        self._seen.append(link_label)
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

        return "".join(escaped.get(c,c) for c in text)


class JiraLinkBot(LinkBot):
    """Subclass LinkBot to customize response for JIRA links

    """
    def message(self, link_label):
        msg = super(JiraLinkBot, self).message(link_label)
        try:
            jira = saml.UwSamlJira()
            issue = jira.issue(link_label)
            summary = issue.fields.summary
            get_name = lambda person: person and person.displayName or 'None'
            reporter = '*Reporter* ' + get_name(issue.fields.reporter)
            assignee = '*Assignee* ' + get_name(issue.fields.assignee)
            status = '*Status* ' + issue.fields.status.name
            lines = list(map(self._escape_html,
                             [summary, reporter, assignee, status]))
            msg = '\n> '.join([msg] + lines)
        except Exception as e:
            print(e)
        return msg


def linkbot():
    """Establish Slack connection and filter messages
    
    """
    try:
        slack = Slacker(getattr(linkconfig, 'API_TOKEN'))
        robo_id = slack.auth.test().body.get('user_id')
        saml.CREDENTIALS = getattr(linkconfig, 'UW_SAML_CREDENTIALS', ())
        response = slack.rtm.start()
        websocket = create_connection(response.body['url'])

        link_bots = []
        for bot_conf in getattr(linkconfig, 'LINKBOTS', []):
            bot_class = globals()[bot_conf.get('LINK_CLASS', 'LinkBot')]
            link_bots.append(bot_class(bot_conf))

        if not len(link_bots):
            raise Exception('No linkbots defined')

        while True:
            try:
                rcv = websocket.recv()
                j = json.loads(rcv)

                if j['type'] == 'message':
                    if j.get('bot_id'):  # ignore all bots
                        continue

                    for bot in link_bots:
                        for match in bot.match(j['text']):
                            print(j['text']+ " match!")
                            try:
                                slack.chat.post_message(
                                    j['channel'],
                                    bot.message(match[1]),
                                    as_user=robo_id,
                                    parse='none')
                            except LinkBotSeenException:
                                pass
                        bot.reset()
            except KeyError:
                pass

    except Exception as ex:
        print('EXCEPTION: %s' % ex)
        pass

    websocket.close()


if __name__ == '__main__':
    linkbot()
