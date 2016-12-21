#!/usr/bin/env python2.7

import argparse

from googleapiclient.errors import HttpError

from oauth import get_service_account_auth


def start_survey(surveys_service, survey_id, max_cost_per_response):
    """Sends the survey to the review process and it is then started.

    Args:
        surveys_service: The Surveys Service used to send the HTTP request.
        survey_id: The id of the survey to start.
        max_cost_per_response: Maximum cost to pay for incidence pricing
                               responses. For more details, visit
                               https://developers.google.com/surveys/v2/reference/surveys.
    """
    if max_cost_per_response:
        json_spec = {'maxCostPerResponseNanos': max_cost_per_response}
    else:
        json_spec = {}
    surveys_service.surveys().start(resourceId=survey_id, body=json_spec).execute()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('survey_id',
                        help='Survey ID to operate on.')
    parser.add_argument('--max_cost_per_response',
                        default=0,
                        help='Maximum cost to pay for incidence pricing responses. Defaults to 0.')
    args = parser.parse_args()

    try:
        start_survey(get_service_account_auth(),
                     args.survey_id,
                     args.max_cost_per_response)
    except HttpError, e:
        print 'Error starting survey: %s\n' % e
    else:
        print 'Started survey %s.\n' % args.survey_id
