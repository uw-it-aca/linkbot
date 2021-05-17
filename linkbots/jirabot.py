from linkbots import LinkBot as LinkBotBase
from datetime import datetime
from six.moves.urllib.parse import quote
from types import SimpleNamespace
from . import saml


class UwSamlJira:
    """A Jira client with a saml session to handle authn on an SSO redirect"""
    def __init__(self, host='', auth=(None, None)):
        """Initialize with the basic auth so we use our _session."""
        self._session = saml.UwSamlSession(credentials=auth)
        self.host = host

    def issue(self, issue_number):
        """
        Return a JIRA issue. Try to adhere to the same model as the
        jira package.
        """
        url = "{}/rest/api/latest/issue/{}".format(
            self.host, quote(issue_number))
        response = self._session.get(url)
        if response.status_code == 404:
            raise KeyError("{} not found".format(issue_number))

        response.raise_for_status()
        data = response.json()

        fields = SimpleNamespace(**data['fields'])
        subobjects = ['status', 'reporter', 'assignee']
        for subobject in subobjects:
            objdict = getattr(fields, subobject, None)
            if objdict:
                setattr(fields, subobject, SimpleNamespace(**objdict))
        return SimpleNamespace(fields=fields)


class LinkBot(LinkBotBase):
    """Subclass LinkBot to customize response for JIRA links

    """
    default_match = '[A-Z]{3,}\-[0-9]+'

    def __init__(self, conf):
        if 'LINK' not in conf:
            conf['LINK'] = '<{}/browse/%s|%s>'.format(conf['HOST'])
        super(LinkBot, self).__init__(conf)
        self.jira = UwSamlJira(host=conf.get('HOST'),
                               auth=conf.get('AUTH'))

    @staticmethod
    def pretty_update_time(issue):
        updated = issue.fields.updated
        try:
            update_dt = datetime.strptime(updated, '%Y-%m-%dT%H:%M:%S.%f%z')
            updated = update_dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
        return updated

    def _get_name(person):
        return person and person.displayName or 'None'

    def message(self, link_label):
        msg = super(LinkBot, self).message(link_label)
        issue = self.jira.issue(link_label)
        summary = issue.fields.summary
        reporter = '*Reporter* ' + self._get_name(issue.fields.reporter)
        assignee = '*Assignee* ' + self._get_name(issue.fields.assignee)
        updated = '*Last Update* ' + self.pretty_update_time(issue)
        status = '*Status* ' + issue.fields.status.name
        lines = list(map(self._escape_html,
                         [summary, reporter, assignee, status, updated]))
        return '\n> '.join([msg] + lines)
