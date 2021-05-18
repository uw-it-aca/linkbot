from random import choice
from metrics import metrics_counter
import re


class LinkBot(object):
    """Implements Slack message matching and link response

    """
    QUIPS = [
        '{}',
        'linkbot noticed a link! {}',
        'Oh, here it is... {}',
        'Maybe this, {}, will help?',
        'Click me! {}',
        'Click my shiny metal link! {}',
        'Here, let me link that for you... {}',
        'Couldn\'t help but notice {} was mentioned...',
        'Not that I was eavesdropping, but did you mention {}?',
        'hmmmm, did you mean {}?',
        '{}...  Mama said there\'d be days like this...',
        '{}?  An epic, yet approachable tale...',
        '{}?  Reminds me of a story...',
    ]
    default_match = r'_THIS_COULD_BE_OVERRIDDEN_'

    def __init__(self, conf):
        self._conf = conf
        match = conf.get('MATCH', self.default_match)
        self._regex = re.compile(r'(\A|\W)+({})'.format(match), flags=re.I)
        self._quips = conf.get('QUIPS', self.QUIPS)
        self._link = conf.get('LINK', '{}|{}')
        self._quiplist = []

    def name(self):
        return "linkbot ({})".format(self.match_pattern())

    def match_regex(self):
        return self._regex

    def match_pattern(self):
        return self._regex.pattern

    def match(self, text):
        """Return a set of unique matches for text."""
        return set(match[1] for match in self._regex.findall(text))

    def message(self, link_label):
        return self._message_text(self._link.format(link_label, link_label))

    def send_message(self, message, say):
        for match in self.match(message.get('text', '')):
            say(self.message(match), parse='none')
            metrics_counter(message.get('channel'))

    def _quip(self, link):
        try:
            if len(self._quiplist) < 1:
                self._quiplist = self._quips.copy()

            quip = choice(self._quiplist)
            self._quiplist.remove(quip)
            return quip.format(link)
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
