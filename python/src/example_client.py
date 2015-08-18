#% Do we need a copyright?

#% make a big comment here with example usages for a couple diff use cases

import argparse
import httplib2
import json
import os

from apiclient.discovery import build_from_document

from oauth2client import client
from oauth2client import tools
from oauth2client import file as oauth_file
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import OAuth2Credentials
from oauth2client.client import SignedJwtAssertionCredentials

BOT_SECRETS = 'robot_account_secret.json'
CLIENT_SECRETS = 'client_secrets.json'
OAUTH2_STORAGE = 'oauth2.dat'
SCOPES = [
    'https://www.googleapis.com/auth/consumersurveys',
    'https://www.googleapis.com/auth/consumersurveys.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--owner_emails',
                        nargs='+',
                        #% Indicate which operations those are required for?
                        help='list of the survey owners.')
    parser.add_argument('--completed_survey_id',
                        help='survey id to retrieve excel results for.')
    parser.add_argument('--start_survey_id',
                        help='survey id to start the survey.')
    parser.add_argument('--results_file',
                        default='results.xls',
                        help='filename to store excel results.')
    parser.add_argument('--robo_email',
                        help='service account email.')

    # Arguments required by tools.run_flow
    parser.add_argument('--logging_level',
                        default='INFO',
                        help='default logging level to use.')
    parser.add_argument('--auth_host_name',
                        default='localhost',
                        help='Hostname for redirects during the OAuth flow.')
    parser.add_argument('--auth_host_port',
                        default=[8080],
                        help='Port for redirects during the OAuth flow.')
    parser.add_argument('--noauth_local_webserver',
                        action='store_true',
                        default=False,
                        help='Run a local webserver to handle redirects.')

    args = parser.parse_args()
    auth_http = setup_auth(args)

    # Load the local copy of the discovery document
    f = file(os.path.join(
        os.path.dirname(__file__),
        "consumersurveys_v2beta_discovery.json"), "r")
    discovery_file = f.read()
    f.close()

    # Construct a service from the local documents
    cs = build_from_document(service=discovery_file, http=auth_http)
    #% do we need to do any checks that the document was read correctly and output errors if not?

    if not args.completed_survey_id and not args.owner_emails and not args.start_survey_id:
        print ('Missing at least one required argument: '
               'Please use owner_emails or completed_survey_id '
               'or startSurveyId flags.')
        return

    if args.start_survey_id:
        start_survey(cs, args.start_survey_id)

    if args.completed_survey_id:
        get_survey_results(
            cs,
            args.completed_survey_id,
            args.results_file)

    if args.owner_emails:
        survey = create_survey(cs, args.owner_emails)
        if survey:
            #% Should this be a separate command?
            update_survey_response_count(cs, survey['surveyUrlId'], 120)
            print 'New Survey Id', survey['surveyUrlId']
        else:
            #% do we get any error codes or reasons?  Would be great to have those throughout.
            print 'Failed to create survey.'


def get_survey(cs, survey_id):
    return cs.surveys().get(surveyUrlId=survey_id).execute()


def start_survey(cs, start_survey_id):
    #% to ops queue FOR verification before starting
    """Sends to survey to ops queue to verification and start.

    Args:
        cs: The cunsumer survey service used to send the HTTP requests.
        start_survey_id: The survey id for which we are startign the survey.

    Returns:
        A dictionary containing the survey id of the started survey.
    """
    json_spec = {'state': 'running'}
    startedSurvey = cs.surveys().update(surveyUrlId=start_survey_id, body=json_spec).execute()
    return startedSurvey


def get_survey_results(cs, completed_survey_id, result_file):
    """Writes the survey results into a xls file.

    Args:
        cs: The cunsumer survey service used to send the HTTP requests.
        completed_survey_id: The survey id for which we are downloading the
            survey results for.
        result_file: The file name which we write the survey results to.
    """
    f = open(result_file, 'w')
    f.write(cs.results().get_media(surveyUrlId=completed_survey_id).execute())


def create_survey(cs, owner_emails):
    """Creates a new survey using a json object containing necessary
       survey fields.

    Args:
        cs: The cunsumer survey service used to send the HTTP requests.
        owner_emails: The list of owners that will be in the newly created
            survey.
    Returns:
        A dictionary containing the survey id of the created survey.
    """
    print "___________", owner_emails
    #% is it possible to use the ROSY spec that Michael checked in instead of JSON?
    json_spec = {
        'title': 'Phone purchase survey',
        'description': 'What phones do people buy and how much do they pay?',
        'owners': owner_emails,
        'wanted_response_count': 100,
        'audience': {
            'country': 'US',
        },
        'questions': [
            {
                'low_value': '1',
                'placeholder': 'enter amount here',
                'question': 'How much did you pay for your last phone?',
                'single_line': True,
                'type': 'open-numeric',
                'units': '$',
                'units_position': 'before',
            }
        ]
    }
    body_def = {'jsonSpec': json.dumps(json_spec)}
    survey = cs.surveys().insert(body=body_def).execute()
    return survey


def update_survey_response_count(cs, survey_id, new_response_count):
    """Updated the response count of the survey.

    Args:
        cs: The cunsumer survey service used to send the HTTP requests.
        survey_id: The survey id for which we are updating the response count
            for.
        new_response_count: An integer specifing the new response count for
            the survey.

    Returns:
        A dictionary containing the survey id of the updated survey.
    """
    json_spec = {'wanted_response_count': new_response_count}
    body_def = {'jsonSpec': json.dumps(json_spec)}
    updatedSurvey = cs.surveys().update(surveyUrlId=survey_id, body=body_def).execute()
    return updatedSurvey


def setup_auth(args):
    """Set up and authentication httplib.

    Args:
        args: ArgumentParser with additional command-line flags to pass to
            the OAuth authentication flow.

    Returns:
        An http client library with authentication enabled.
    """
    # Perform OAuth 2.0 authorization.

    # Service accounts will follow the following authenication.
    if args.robo_email:
        client_email = args.robo_email
        with open(BOT_SECRETS) as f:
          private_key = json.loads(f.read())['private_key']
        credentials = client.SignedJwtAssertionCredentials(client_email, private_key,
            scope=SCOPES)
    else:
        flow = flow_from_clientsecrets(CLIENT_SECRETS, scope=SCOPES)
        storage = oauth_file.Storage(OAUTH2_STORAGE)
        credentials = storage.get()

        if credentials is None or credentials.invalid:
            credentials = tools.run_flow(flow, storage, args)

    http = httplib2.Http()
    auth_http = credentials.authorize(http)
    #% i suspect this will be where most first time users get a failure -- can we print helpful errors for the various things that could go wrong?
    return auth_http


if __name__ == '__main__':
    main()
