#!/usr/bin/env python2.7

import httplib2
from googleapiclient.discovery import build
from oauth2client import clientsecrets
from oauth2client.service_account import ServiceAccountCredentials


def get_service_account_auth():
    # [START google_surveys_auth]
    json_keyfile_name = 'account_secret.json'
    scopes = [
        'https://www.googleapis.com/auth/surveys',
        'https://www.googleapis.com/auth/surveys.readonly',
        'https://www.googleapis.com/auth/userinfo.email',
    ]

    try:
        credentials = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_name, scopes)
        http = httplib2.Http()
        auth_http = credentials.authorize(http)
    except clientsecrets.InvalidClientSecretsError, e:
        print ('Unable to setup authorization with the given credentials.  %s'
               % e)
        return

    surveys_service = build('surveys', 'v2', http=auth_http)
    # [END google_surveys_auth]

    return surveys_service
