from linkbot import linkbot_bot_list
import logging


def linkbot_command(ack, say, command, logger):
    ack()
    parts = command.get('text', '').split()
    op = parts[0].lower()
    argv = parts[1:]
    if len(argv) == 0 or op in ['help', '?']:
        say("linkbot can:\n{}".format('   \n'.join([
            "debug [on|off]",
            "quips [on|off|reset]",
            "links"])))
    elif op == 'debug':
        sense = argv[0].lower() in ['on', '1', 'true']
        logger.setLevel(logging.DEBUG if sense else logging.INFO)
        say("linkbot debug logging {}".format('on' if sense else 'off'))
    elif op == 'quips':
        arg = argv[0].lower()
        if arg == 'reset':
            for bot in linkbot_bot_list():
                bot.quip_reset()

            say("linkbot quips have been reset")
        else:
            sense = arg in ['on', '1', 'true']
            for bot in linkbot_bot_list():
                bot.quip = sense

            say("linkbot turned {} quips".format('on' if sense else 'off'))
    elif op == 'links':
        say("linkbot searches for:\n".format("    \n".join(
            ["{}: {}".format(bot.name(), bot.match_pattern())
             for bot in linkbot_bot_list()])))
    else:
        say("sorry, linkbot cannot *{}*".format(op))

