#!/usr/bin/env python2.7

import pprint

from googleapiclient.errors import HttpError

from oauth import get_service_account_auth


def list_surveys(surveys_service):
    """Prints the surveys that are owned by the given user.

    Args:
        surveys_service: The Surveys Service used to send the HTTP request.
    """

    # [START google_surveys_list]
    surveys = surveys_service.surveys().list().execute()
    # [END google_surveys_list]

    return surveys

if __name__ == '__main__':
    try:
        results = list_surveys(get_service_account_auth())
    except HttpError, e:
        print 'Error listing surveys: %s\n' % e
    else:
        for s in results.get('resources'):
            pprint.pprint(s)
