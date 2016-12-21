#!/usr/bin/env python2.7

import argparse
import pprint

from googleapiclient.errors import HttpError

from oauth import get_service_account_auth


def get_survey(surveys_service, survey_id):
    """Gets a survey.

    Args:
        surveys_service: The Survey Service used to send the HTTP request.
        survey_id: The id of the survey to get.

    Returns:
        A dictionary containing the survey fields.
    """
    return surveys_service.surveys().get(surveyUrlId=survey_id).execute()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('survey_id',
                        help='Survey ID to operate on.')
    args = parser.parse_args()

    try:
        survey_results = get_survey(get_service_account_auth(), args.survey_id)
    except HttpError, e:
        print 'Error fetching survey: %s\n' % e
    else:
        pprint.pprint(survey_results)
