from setuptools import setup

README = """
See the README on `GitHub
<https://github.com/uw-it-aca/linkbot>`_.
"""

url = "https://github.com/uw-it-aca/linkbot"
setup(
    name='linkbot',
    author="UW-IT AXDD",
    author_email="aca-it@uw.edu",
    install_requires=[
        'beautifulsoup4',
        'simplejson',
        'slack_bolt',
        'requests',
        'django-prometheus'],
    license='Apache License, Version 2.0',
    description='slackbot listening for mentions of jira issues, etc',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
    ],
)
