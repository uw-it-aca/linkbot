import logging


def linkbot_command(ack, say, command, logger):
    from linkbot import bot_list

    ack()
    parts = command.get('text', '').split()
    op = parts[0].lower() if len(parts) > 0 else ''
    argv = parts[1:] if len(parts) > 1 else [None]
    if op in ['help', '?', '']:
        say("linkbot can:\n{}".format('   \n'.join([
            "debug [on|off]",
            "quips [on|off|reset]",
            "links"])), parse='none')
    elif op == 'debug':
        if argv[0]:
            sense = argv[0].lower() in ['on', '1', 'true']
            logger.setLevel(logging.DEBUG if sense else logging.INFO)
            say("linkbot debug logging {}".format('on' if sense else 'off'),
                parse='none')
        else:
            say("linkbot debug is {}".format(logger.level == logging.DEBUG))
    elif op == 'quips':
        if argv[0]:
            arg = argv[0].lower()
            if arg == 'reset':
                for bot in bot_list:
                    bot.quip_reset()

                say("linkbot quips have been reset")
            elif arg in ['on', 'off', 'true', 'false', '0', '1']:
                sense = arg in ['on', '1', 'true']
                for bot in bot_list:
                    bot.quip = sense

                say("linkbot turned {} quips".format('on' if sense else 'off'))
            else:
                say("unrecognized quips option")
        else:
            q = set()
            for bot in bot_list:
                for bq in bot.QUIPS:
                    q.add(bq)

            say("Current set of quips:\n".format("    \n".join(q)),
                parse='none')
    elif op == 'links':
        if argv[0] is None:
            say("linkbot searches for:\n".format("    \n".join(
                ["{}: {}".format(bot.name(), bot.match_pattern())
                 for bot in bot_list])), parse='none')
        else:
            say("unrecognized links option")
    else:
        say("sorry, linkbot cannot *{}*".format(op))

