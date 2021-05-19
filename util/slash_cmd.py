# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0
"""
Class implementing linkbot Slack slash command
"""
import logging


class SlashCommand:
    name = "linkbot"

    OPERATIONS = [
        {'name': ['help', '?', ''],
         'method': 'op_help',
         'description': "*[help|?|]* Offer this helpful message" },
        {'name': ['debug'],
         'method': 'op_debug',
         'description': "*debug [on|off]* Adjust verbose logging" },
        {'name': ['quips'],
         'method': 'op_quips',
         'description': "*quips [on|off|reset]* Control link quip display"},
        {'name': ['links'],
         'method': 'op_links',
         'description': "*links* Show links I'm looking for"}
    ]

    def __init__(self, *args, **kwargs):
        self._bot_list = kwargs.get('bot_list', [])
        self._logger = kwargs.get('logger', logging.getLogger(__name__))

    def command(self, command, say, ack):
        ack()
        parts = command.get('text', '').split()
        op = parts[0].lower() if len(parts) > 0 else ''
        argv = parts[1:] if len(parts) > 1 else [None]

        for operation in self.OPERATIONS:
            if op in operation['name']:
                return getattr(self, operation['method'])(argv, say)

        say("sorry, linkbot cannot *{}*".format(op))

    def op_help(self, argv, say):
        self._indented_list(say, "Hi! I'm linkbot and I can", [
            op['description'] for op in self.OPERATIONS])

    def op_debug(self, argv, say):
        if argv[0]:
            try:
                self._logger.setLevel(logging.DEBUG if (
                    self._boolean(argv[0])) else logging.INFO)
            except Exception as ex:
                say("{} debug: {}".format(self.name, ex))

        say("linkbot debug is {}".format(
            self._boolean_state(self._logger.level == logging.DEBUG)))

    def op_quips(self, argv, say):
        if argv[0]:
            sub_op = argv[0].lower()
            if sub_op == 'reset':
                for bot in self._bot_list:
                    bot.quip_reset()

                say("linkbot quips have been reset")
            else:
                try:
                    sense = self._boolean(sub_op)
                    for bot in self._bot_list:
                        bot.quip = sense

                    say("Linkbot turned {} quips".format(
                        self._boolean_state(sense)))
                except Exception as ex:
                    say("{} quips: {}".format(self.name, ex))
        else:
            q = set()
            for bot in self._bot_list:
                if bot.quip:
                    for bq in bot.QUIPS:
                        q.add(bq)

            if len(q) > 0:
                self._indented_list(say, "Current quips include", q)
            else:
                say("Quips are currently turned off")

    def op_links(self, argv, say):
        if argv[0] is None:
            links = ["{}: {}".format(
                bot.name(), bot.escape_html(bot.match_pattern()))
                     for bot in self._bot_list]
            self._indented_list(say, 'Linkbot link searches', links)
        else:
            say("unrecognized links option")

    def _indented_list(self, say, title, l, indent="> "):
        delim = "\n{}".format(indent)
        say("{}:{}{}".format(title, delim, delim.join(l)), parse='none')

    def _boolean(self, arg):
        b = arg.lower()
        if b in ['on', 'off', 'true', 'false', '0', '1', 'yes', 'no']:
            return b in ['on', '1', 'true', 'yes']
        else:
            raise Exception("invalid boolean value {}".format(arg))

    def _boolean_state(self, value):
        return 'on' if value else 'off'
