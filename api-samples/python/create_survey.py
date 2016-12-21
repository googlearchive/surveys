#!/usr/bin/env python2.7

import argparse

from googleapiclient.errors import HttpError

from oauth import get_service_account_auth


def create_survey(surveys_service, owner_emails):
    """Creates a new survey using a json object containing necessary survey fields.

    Args:
        surveys_service: The Surveys service used to send the HTTP request.
        owner_emails: List of survey owner emails for a new survey.
    Returns:
        A dictionary containing the survey id of the created survey.
    """
    body_def = {
        'title': 'Student cell phone ownership',
        'description': 'Ownership of cell phones, targeted towards students.',
        'owners': owner_emails,
        'wantedResponseCount': 100,
        'audience': {
            'country': 'US',
            'languages': ['en-US'],
            'populationSource': 'androidAppPanel',
            'mobileAppPanelId': 'agxzfjQwMi10cmlhbDJyIAsSCVBhbmVsSW5mbyIRc3R1ZGVudHNfdmVyaWZpZWQM',
        },
        'questions': [
            {
                'question': 'Do you own a cell phone?',
                'type': 'singleAnswer',
                'answers': [
                    'Yes',
                    'No'],
                'thresholdAnswers': [
                    'Yes'],
            },
            {
                'question': 'What type of cell phone do you own?',
                'type': 'singleAnswer',
                'answers': [
                    'Android phone',
                    'iPhone',
                    'Other'],
                'thresholdAnswers': [
                    'Android phone'],
            },
            {
                'question': 'What brand is your Android phone?',
                'type': 'singleAnswer',
                'answers': [
                    'Google',
                    'Samsung',
                    'LG',
                    'Other'],
            }
        ]
    }

    return surveys_service.surveys().insert(body=body_def).execute()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('owner_email',
                        nargs='+',
                        help='List of survey owner emails (space separated) for a new survey.')
    args = parser.parse_args()

    try:
        survey = create_survey(get_service_account_auth(), args.owner_email)
    except HttpError, e:
        print 'Error creating survey: %s\n' % e
    else:
        print 'Successully created survey with id %s\n' % survey['surveyUrlId']
