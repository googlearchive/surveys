#!/usr/bin/env python2.7

import httplib2
from googleapiclient.discovery import build
from oauth2client import clientsecrets
from oauth2client.service_account import ServiceAccountCredentials

ACCOUNT_SECRET = 'account_secret.json'
SCOPES = [
    'https://www.googleapis.com/auth/surveys',
    'https://www.googleapis.com/auth/surveys.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
]


def setup_auth():
    """Set up and authenticate HTTP client library.

    Returns:
        An HTTP client library with authentication enabled.
    """
    credentials = ServiceAccountCredentials.from_json_keyfile_name(ACCOUNT_SECRET, SCOPES)
    http = httplib2.Http()
    return credentials.authorize(http)


def get_service_account_auth():
    try:
        auth_http = setup_auth()
    except clientsecrets.InvalidClientSecretsError, e:
        print ('Unable to setup authorization with the given credentials.  %s'
               % e)
        return

    return build('surveys', 'v2', http=auth_http)
