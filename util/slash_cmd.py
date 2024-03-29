# Copyright 2023 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

# Copyright 2022 UW-IT, University of Washington
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
         'description': "*[help|?|]* Offer this helpful message"},
        {'name': ['debug'],
         'method': 'op_debug',
         'description': "*debug [on|off]* Adjust verbose logging"},
        {'name': ['quips'],
         'method': 'op_quips',
         'description': "*quips [on|off|reset]* Control link quip display"},
        {'name': ['links'],
         'method': 'op_links',
         'description': "*links* Show links I'm looking for"}
    ]

    _client = None
    _channel_id = None
    _user_id = None

    def __init__(self, *args, **kwargs):
        self._bot_list = kwargs.get('bot_list', [])
        self._logger = kwargs.get('logger', logging.getLogger(__name__))

    def command(self, command, client, ack):
        ack()

        self._client = client
        self._channel_id = command.get('channel_id')
        self._user_id = command.get('user_id')
        parts = command.get('text', '').split()
        op = parts[0].lower() if len(parts) > 0 else ''
        argv = parts[1:] if len(parts) > 1 else [None]

        for operation in self.OPERATIONS:
            if op in operation['name']:
                return getattr(self, operation['method'])(argv)

        self._post("sorry, linkbot cannot *{}*".format(op))

    def op_help(self, argv):
        self._indented_list("Hi! I'm linkbot and I can", [
            op['description'] for op in self.OPERATIONS])

    def op_debug(self, argv):
        if argv[0]:
            try:
                self._logger.setLevel(logging.DEBUG if (
                    self._boolean(argv[0])) else logging.INFO)
            except Exception as ex:
                self._post("{} debug: {}".format(self.name, ex))

        self._post("linkbot debug is {}".format(
            self._boolean_state(self._logger.level == logging.DEBUG)))

    def op_quips(self, argv):
        if argv[0]:
            sub_op = argv[0].lower()
            if sub_op == 'reset':
                for bot in self._bot_list:
                    bot.quip_reset()

                self._post("linkbot quips have been reset")
            else:
                try:
                    sense = self._boolean(sub_op)
                    for bot in self._bot_list:
                        bot.quip = sense

                    self._post("Linkbot turned {} quips".format(
                        self._boolean_state(sense)))
                except Exception as ex:
                    self._post("{} quips: {}".format(self.name, ex))
        else:
            q = set()
            for bot in self._bot_list:
                if bot.quip:
                    for bq in bot.QUIPS:
                        q.add(bot.escape_html(bq.format("<LINK>")))

            if len(q) > 0:
                self._indented_list("Current quips include", q)
            else:
                self._post("Quips are currently turned off")

    def op_links(self, argv):
        if argv[0] is None:
            links = ["*{}* {}".format(
                bot.name(), bot.escape_html(bot.match_pattern()))
                     for bot in self._bot_list]
            self._indented_list('Linkbot link searches', links)
        else:
            self._post("unrecognized links option")

    def _indented_list(self, title, l, indent="> "):
        delim = "\n{}".format(indent)
        self._post("{}:{}{}".format(title, delim, delim.join(l)))

    def _post(self, text):
        self._client.chat_postEphemeral(text=text,
                                        user=self._user_id,
                                        channel=self._channel_id,
                                        arse="none")

    def _boolean(self, arg):
        b = arg.lower()
        if b in ['on', 'off', 'true', 'false', '0', '1', 'yes', 'no']:
            return b in ['on', '1', 'true', 'yes']
        else:
            raise Exception("invalid boolean value {}".format(arg))

    def _boolean_state(self, value):
        return 'on' if value else 'off'
