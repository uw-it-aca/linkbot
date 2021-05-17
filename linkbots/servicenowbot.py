from linkbots import LinkBot as LinkBotBase
from urllib.parse import urlencode
from functools import partial
import requests
import collections
import re


class ServiceNowClient(requests.Session):
    """ServiceNow REST client for looking up records."""
    api = '/api/now/table'
    table_map = {
        'CHG': 'change_request',
        'CTASK': 'change_task',
        'INC': 'incident',
        'ITASK': 'u_incident_task',
        'PRB': 'problem',
        'PTASK': 'problem_task',
        'REQ': 'u_simple_requests',
        'RTASK': 'u_request_task',
    }
    _digits_regex = re.compile('[0-9]')

    def __init__(self, host='', auth=()):
        """Initialize ServiceNowClient with a host and user/password tuple."""
        super(ServiceNowClient, self).__init__()
        self.headers.update({"Content-Type": "application/json",
                            "Accept": "application/json"})
        self.auth = auth
        self.host = host

    def get_number(self, number, full_payload=False):
        """Look up a service now record based on its number (eg REQ0000001).
        Return a ServiceNowRecord with, the attributes of which are controlled
        by ServiceNowRecord.fields, unless full_payload, in which case return
        all the attributes.
        """
        table = self._table_from_number(number)
        url = self.host + self.api
        fields = []
        if not full_payload:
            fields = ServiceNowRecord.fields
        query = {
            'sysparm_query': 'number={num}'.format(num=number),
            'sysparm_display_value': 'true',
            'sysparm_limit': '1',
            'sysparm_fields': ','.join(fields)
        }
        url += '/{table}?{query}'.format(table=table, query=urlencode(query))
        response = self.get(url)
        if response.status_code != 200:
            raise IOError('bad service now response ' + str(response))
        result = next(iter(response.json()['result']), None)
        if not result:
            raise KeyError(number + ' not found')
        return ServiceNowRecord(**result)

    def link(self, number):
        """Return a link to a record given its number."""
        fargs = {'host': self.host, 'table': self._table_from_number(number),
                 'number': number}
        return ('{host}/{table}.do?sysparm_table={table}'
                '&sysparm_query=number%3D{number}').format(**fargs)

    def _table_from_number(self, number):
        """Given a number, parse out the record type and return the matching
        table if there is one.
        """
        ticket_type = self._digits_regex.sub('', number)
        table = self.table_map.get(ticket_type)
        if not table:
            raise KeyError('unrecognized service now type ' + ticket_type)
        return table


class ServiceNowRecord:
    """A record returned from ServiceNowClient. The default fields are ones
    deemed interesting to summarize a record.
    """
    fields = {
        'short_description': 'Subject',
        'number': 'Number',
        'parent': 'Parent',
        'state': 'State',
        'assigned_to': 'Assigned To',
        'opened_by': 'Opened By',
        'sys_updated_on': 'Last Update'}

    def __init__(self, **kwargs):
        self.__dict__ = kwargs

    def __repr__(self):
        inner = ', '.join(map(partial(str.join, '='), self.items()))
        return 'ServiceNowRecord({inner})'.format(inner=inner)

    def items(self, pretty_names=False):
        """Yield the key/value tuples of the the record. If pretty_names,
        change the key to a user-facing value. If value is an object,
        check display_value for a more friendly value.
        """
        for field in self.fields:
            value = getattr(self, field)
            is_mapping = isinstance(value, collections.Mapping)
            if is_mapping and 'display_value' in value:
                value = value.get('display_value')
            if pretty_names:
                field = self.fields.get(field, field)
            yield field, value


class LinkBot(LinkBotBase):
    _ticket_regex = '|'.join(ServiceNowClient.table_map)
    default_match = '({})[0-9]{7,}'.format(_ticket_regex)

    def __init__(self, conf):
        super(LinkBot, self).__init__(conf)
        self.client = ServiceNowClient(
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
