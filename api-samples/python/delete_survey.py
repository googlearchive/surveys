#!/usr/bin/env python2.7

import argparse

from googleapiclient.errors import HttpError

from oauth import get_service_account_auth


def delete_survey(surveys_service, survey_id):
    """Deletes a survey.

    Args:
        surveys_service: The Survey Service used to send the HTTP request.
        survey_id: The id of the survey to delete.
    """

    # [START google_surveys_delete]
    surveys_service.surveys().delete(surveyUrlId=survey_id).execute()
    # [END google_surveys_delete]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('survey_id',
                        help='Survey ID to operate on.')
    args = parser.parse_args()

    try:
        delete_survey(get_service_account_auth(), args.survey_id)
    except HttpError, e:
        print 'Error deleting survey: %s\n' % e
    else:
        print 'Successully deleted survey with id %s\n' % args.survey_id
