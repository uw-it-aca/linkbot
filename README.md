# linkbot
Slackbot to bind message fragments to external links

Linkbot can run anwhere. To get it running, just create it's configuration module, `linkconfig.py`, and supply
the following module variables:

### Example `linkconfig.py`

    API_TOKEN='_API_Token_generated_from_your_Slack_instance_'
    UW_SAML_CREDENTIALS = ('_low-privilege-username_', '_password_')
    SERVICE_NOW_CREDENTIALS = ('_api-account_', '_api-key_')
    LINKBOTS = [
        {
            'LINK_CLASS': 'JiraLinkBot',
            'HOST': 'https://jira.cac.washington.edu',
            'AUTH': UW_SAML_CREDENTIALS,
            'MATCH': '[A-Z]{3,}\-[0-9]+',
            'LINK': '<https://jira.example.edu/browse/%s|%s>',
        },
        {
            'LINK_CLASS': 'ServiceNowBot',
            'HOST': 'https://XXXX.service-now.com',
            'AUTH': SERVICE_NOW_CREDENTIALS,
            'MATCH': '(REQ|INC|ITASK|RTASK)[0-9]{7,}'
        }
    ]

See [Slack Help](https://get.slack.help/hc/en-us/articles/215770388-Create-and-regenerate-API-tokens) for guidance on generating the value for API_TOKEN

The LINKBOTS list can be any number of dicts supplying, minimally, a `MATCH` and `LINK` key.

`MATCH` is a regular expression that defines what to look for in Slack messages.

`LINK` provides the link and link text linkbot uses in its response.  The format
consists of a link and link text enclosed in angle brackets and separated by the pipe character as in the example above.  Two 
instances of print format characters, %s, are used by linkbot to insert the matched text in the SLACK message in the first, and 
a randomly selected quip in the second.

It's a pretty simple little script.  Pull requests are welcome!

