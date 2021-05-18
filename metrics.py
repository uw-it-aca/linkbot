from prometheus_client import start_http_server, Counter

# prepare metrics
linkbot_message_count = Counter(
    'message_sent_count',
    'LinkBot message match and sent count',
    ['channel'])


def metrics_counter(channel):
    linkbot_message_count.labels(channel).inc()


def metrics_server(port):
    start_http_server(port)
