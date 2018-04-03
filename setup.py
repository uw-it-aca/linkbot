from setuptools import setup

install_requires = ['beautifulsoup4',
                    'simplejson',
                    'slacker',
                    'jira',
                    'requests',
                    'websocket-client']

setup(name='linkbot',
      install_requires=install_requires,
      description='slackbot listening for mentions of jira issues, etc')
