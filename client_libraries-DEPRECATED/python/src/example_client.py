#!/usr/bin/env python2.7

# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Command-line tool for interacting with the Google Surveys API.

To run, generate a client secret using https://console.developers.google.com/
under the APIs and Auth Tab for your project. Then download the JSON object
and save it as client_secrets.json

For more instructions on how to obtain the local files necessary for OAuth
authorization, please see https://github.com/google/surveys

Install the Google APIs Client Library for Python:
$ pip install --upgrade google-api-python-client

To create a survey:
$ ./example_client.py create --owner_email <email1> <email2> \
    --client_secrets_file <file>

To start the survey:
$ ./example_client.py start --survey_id <id> --client_secrets_file <file>

To download survey results:
$ ./example_client.py fetch --survey_id <id> --results_file=~/my_results.xls \
    --client_secrets_file <file>

Alternatively, to download survey results with a Service Account:
$ ./example_client.py fetch --survey_id <id> --results_file=~/my_results.xls \
    --service_account <email>  --service_account_secrets_file <file>
"""

import argparse
import os
import pprint

import httplib2
from googleapiclient.discovery import build_from_document
from googleapiclient.errors import HttpError
from oauth2client import clientsecrets
from oauth2client import file as oauth_file
from oauth2client import tools
from oauth2client.client import flow_from_clientsecrets
from oauth2client.service_account import ServiceAccountCredentials

_SERVICE_ACCOUNT_SECRETS = 'robot_account_secret.json'
_OAUTH_CLIENT_SECRETS = 'client_secrets.json'
OAUTH2_STORAGE = 'oauth2.dat'
SCOPES = [
    'https://www.googleapis.com/auth/surveys',
    'https://www.googleapis.com/auth/surveys.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
]

# Constants that enumerate the various operations that the client allows.

# Get an existing survey.
_GET = 'get'
# Create a new survey.
_CREATE = 'create'
# List the surveys that this user owns.
_LIST = 'list'
# Fetch the results of an existing survey.
_FETCH = 'fetch'
# Fetch the results of an existing survey.
_START = 'start'

_OPERATIONS = [
    _GET,
    _CREATE,
    _START,
    _FETCH,
    _LIST,
]

_DESCRIPTION = """

You must choose one of the following operations:
  - create: To create a new survey.
  - set_response_count: Set the number of desired responses for a given survey.
  - start: Start the given survey.
  - fetch: Fetch the results in .xls format for a given survey.
  - list: List the surveys that are owned by this user.
  - get: Get the survey definition

For a full list of available flags, use the --help flag.
"""


def main():
    parser = argparse.ArgumentParser(
        usage=_DESCRIPTION,
    )
    parser.add_argument('operation', choices=_OPERATIONS,
                        help='The operation to perform.')
    parser.add_argument('--survey_id',
                        help='Survey ID to operate on.')
    parser.add_argument('--owner_emails',
                        nargs='+',
                        help='List of survey owners (space separated) for a '
                             'new survey.')
    parser.add_argument('--results_file',
                        default='results.xls',
                        help='filename to store excel results.')
    parser.add_argument('--autostart_max_cost_per_response',
                        default=0,
                        help='Maximum cost to pay for incidence pricing responses.')

    # Service Account flags.
    parser.add_argument('--service_account',
                        help='Service account email to use.  Make sure that '
                             '--service_account_secrets_file is set correctly '
                             '.')
    parser.add_argument('--service_account_secrets_file',
                        default=_SERVICE_ACCOUNT_SECRETS,
                        help='Path to the Service Account secrets JSON file.')

    # OAuth2 client ID flags.
    parser.add_argument('--client_secrets_file',
                        default=_OAUTH_CLIENT_SECRETS,
                        help='Path to the OAuth client secrets JSON file.')

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

    try:
        auth_http = setup_auth(args)
    except clientsecrets.InvalidClientSecretsError, e:
        print ('Unable to setup authorization with the given credentials.  %s'
               % e)
        return

    # Load the local copy of the discovery document
    f = file(os.path.join(
        os.path.dirname(__file__),
        "surveys_v2_discovery.json"), "r")
    discovery_file = f.read()
    f.close()

    # Construct a service from the local documents
    try:
        cs = build_from_document(service=discovery_file, http=auth_http)
    except ValueError, e:
        print 'Error parsing discovery file "%s": %s' % (f.name, e)
        return

    if args.operation == _CREATE:
        if not args.owner_emails:
            parser.error('--owner_emails is required for this operation.')
        survey = create_survey(cs, args.owner_emails)
        if not survey:
            parser.exit(status=1, message='Failed to create survey.\n')
        print 'Successully created survey with id %s\n' % survey['surveyUrlId']
        print 'Once started, you can view survey results here:'
        print ('https://surveys.google.com/reporting/survey'
               '?survey=%s\n' % survey['surveyUrlId'])

    if args.operation == _START:
        if not args.survey_id:
            parser.error('--survey_id is required for this operation.')
        if args.autostart_max_cost_per_response:
            start_survey(cs, args.survey_id, args.autostart_max_cost_per_response)
        else:
            start_survey(cs, args.survey_id)

        print 'You can view survey results here:'
        print ('https://surveys.google.com/reporting/survey'
               '?survey=%s\n' % args.survey_id)

    if args.operation == _FETCH:
        if not args.survey_id:
            parser.error('--survey_id is required for this operation.')
        get_survey_results(
            cs,
            args.survey_id,
            args.results_file)
        print 'You can also view the survey results here:'
        print ('https://surveys.google.com/reporting/survey'
               '?survey=%s\n' % args.survey_id)

    if args.operation == _GET:
        if not args.survey_id:
            parser.error('--survey_id is required for this operation.')
        pprint.pprint(get_survey(cs, args.survey_id))

    if args.operation == _LIST:
        list_surveys(cs)


def get_survey(cs, survey_id):
    """Gets a survey.

    Args:
        cs: The Surveys Service used to send the HTTP requests.
        survey_id: The id of the survey to get.

    Returns:
        A dictionary containing the survey fields.
    """
    result = cs.surveys().get(surveyUrlId=survey_id).execute()
    return result


def list_surveys(cs):
    """Prints the surveys that are owned by the given user.

    Args:
        cs: The Surveys Service used to send the HTTP requests.
    """
    results = cs.surveys().list().execute()
    for s in results.get('resources'):
        pprint.pprint(s)


def start_survey(cs, survey_id, autostart_max_cost_per_response=0):
    """Sends the survey to the review process and it is then started.

    Args:
        cs: The Surveys Service used to send the HTTP requests.
        survey_id: The survey id for which we are starting the survey.

    Returns:
        A dictionary containing the survey id of the started survey.
    """
    if autostart_max_cost_per_response:
        json_spec = {'autostartMaxCostPerResponse': autostart_max_cost_per_response}
        return cs.surveys().start(
            resourceId=survey_id, body=json_spec).execute()
    return cs.surveys().start(resourceId=survey_id, body='{}').execute()


def get_survey_results(cs, survey_id, result_file):
    """Writes the survey results into a xls file.

    Args:
        cs: The Survey Service used to send the HTTP requests.
        survey_id: The survey id for which we are downloading the
            survey results for.
        result_file: The file name which we write the survey results to.
    """
    f = open(result_file, 'wb')
    f.write(cs.results().get_media(surveyUrlId=survey_id).execute())
    print 'Successfully wrote survey %s results to %s\n' % (survey_id,
                                                            result_file)


def create_survey(cs, owner_emails):
    """Creates a new survey using a json object containing necessary
       survey fields.

    Args:
        cs: The Surveys Service used to send the HTTP requests.
        owner_emails: The list of owners that will be in the newly created
            survey.
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
    try:
        survey = cs.surveys().insert(body=body_def).execute()
    except HttpError, e:
        print 'Error creating the survey: %s\n' % e
        return None
    return survey


def setup_auth(args):
    """Set up and authentication httplib.

    Args:
        args: ArgumentParser with additional command-line flags to pass to
            the OAuth authentication flow.

    Returns:
        An http client library with authentication enabled.
    """
    # Perform OAuth 2.0 authorization.
    if args.service_account:
        # Service accounts will follow the following authenication.
        client_email = args.service_account
        secret_file = args.service_account_secrets_file
        if secret_file.endswith('json'):
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                secret_file, SCOPES)
        elif secret_file.endswith('p12'):
            credentials = ServiceAccountCredentials.from_p12_keyfile(
                client_email, secret_file, SCOPES)
        else:
            raise RuntimeError('Credentials file must end with .json or .p12.')

    else:
        flow = flow_from_clientsecrets(args.client_secrets_file, scope=SCOPES)
        storage = oauth_file.Storage(OAUTH2_STORAGE)
        credentials = storage.get()

        if credentials is None or credentials.invalid:
            credentials = tools.run_flow(flow, storage, args)

    http = httplib2.Http()
    return credentials.authorize(http)


if __name__ == '__main__':
    main()
