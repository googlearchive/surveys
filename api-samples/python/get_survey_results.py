#!/usr/bin/env python2.7

import argparse

from googleapiclient.errors import HttpError

from oauth import get_service_account_auth


def get_survey_results(surveys_service, survey_id):
    """Fetches the results of a survey.

    Args:
        surveys_service: The Survey Service used to send the HTTP request.
        survey_id: The survey id for which we are downloading the survey
                   results for.
    """
    return surveys_service.results().get_media(surveyUrlId=survey_id).execute()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('survey_id',
                        help='Survey ID to operate on.')
    parser.add_argument('--results_file',
                        default='results.xls',
                        help='Filename to store results.  Defaults to results.xls.')
    args = parser.parse_args()

    try:
        survey_results = get_survey_results(get_service_account_auth(), args.survey_id)
    except HttpError, e:
        print 'Error fetching survey results: %s\n' % e
    else:
        f = open(args.results_file, 'wb')
        f.write(survey_results)
        print 'Successfully wrote survey %s results to %s\n' % (args.survey_id,
                                                                args.results_file)
