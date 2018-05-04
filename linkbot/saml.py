"""Utilities for working with sites behind UW SSO."""
import requests
from bs4 import BeautifulSoup
from six.moves.urllib.parse import urljoin
IDP = 'https://idp.u.washington.edu/'


class UwSamlSession(requests.Session):
    """A requests.Session that checks responses for IdP redirects."""
    def __init__(self, credentials=(None, None)):
        self._credentials = credentials
        super(UwSamlSession, self).__init__()

    def request(self, method, url, *args, **kwargs):
        """
        For every request that comes in, submit the request and check if we
        got redirected to the IdP for authentication. If so, submit the
        configured credentials and post back to the SP for completion of the
        request.
        """
        request = super(UwSamlSession, self).request
        response = request(method, url, *args, **kwargs)
        for _ in range(2):
            if not response.url.startswith(IDP):
                break
            url, form = self._form_data(response.content)
            if 'j_username' in form:
                user, password = self._credentials
                form.update({
                    'j_username': user,
                    'j_password': password})
            # don't let the client override content-type
            headers = {'Content-Type': None}
            response = request('POST', url=url, data=form, headers=headers)
            if response.status_code != 200:
                raise Exception('saml login failed', response)
        return response

    @staticmethod
    def _form_data(content):
        """Return a tuple of (form url, form data) from response content."""
        bs = BeautifulSoup(content, 'html.parser')
        form = bs.find('form')
        url = urljoin(IDP, form['action'])
        data = {element['name']: element.get('value')
                for element in form.find_all('input')
                if element.get('name')}
        return url, data
