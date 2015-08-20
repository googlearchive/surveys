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

"""Command-line tool for interacting with the Google Consumer Surveys API.

Reads client credential from clients_secrets.json in the current directory,
initiates an OAuth handshake in the user's browser if no valid token is present
, calls the Consumer Surveys API to read the results for a survey, and writes
an Excel file to results.xls in the same directory.

To run, generate a client secret using https://console.developers.google.com/
under the APIs and Auth Tab for your project. Then download the JSON object
and save it as client_secrets.json

Download and install the python Google Oauth Library:
https://code.google.com/p/google-api-python-client/downloads/list

Or install it with PIP:
$ pip install google-api-python-client

TODO: Example on how to run locally.
TODO: Example on how to setup local secrets files.
TODO: Move secrets files to command line flags.


To create a survey:
    ./example_client.py --owner_email <email>


To download survey results:
    ./example_client.py --survey_id <survey_id>
"""

import argparse
import httplib2
import json
import os

from apiclient.discovery import build_from_document
import googleapiclient

from oauth2client import client
from oauth2client import clientsecrets
from oauth2client import tools
from oauth2client import file as oauth_file
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import OAuth2Credentials
from oauth2client.client import SignedJwtAssertionCredentials

_SERVICE_ACCOUNT_SECRETS = 'robot_account_secret.json'
_OAUTH_CLIENT_SECRETS = 'client_secrets.json'
OAUTH2_STORAGE = 'oauth2.dat'
SCOPES = [
    'https://www.googleapis.com/auth/consumersurveys',
    'https://www.googleapis.com/auth/consumersurveys.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
]

# Constants that enumerate the various operations that the client allows.

# Create a new survey.
_CREATE = 'create'
# Set the desired response count of an existing survey.
_SET_RESPONSE_COUNT = 'set_response_count'
# Fetch the results of an existing survey.
_FETCH = 'fetch'
# Fetch the results of an existing survey.
_START = 'start'

_OPERATIONS = [
    _CREATE,
    _SET_RESPONSE_COUNT,
    _START,
    _FETCH,
]

_DESCRIPTION = """

You must choose one of the following operations:
  - create: To create a new survey.
  - set_response_count: Set the number of desired responses for a given survey.
  - start: Start the given survey.
  - fetch: Fetch the results in .xls format for a given survey.

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

    # Service Account flags.
    parser.add_argument('--robo_email',
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
        "consumersurveys_v2beta_discovery.json"), "r")
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
        print 'Once started, survey results will be visible here:'
        print ('https://www.google.com/insights/consumersurveys/view'
               '?survey=%s\n' % survey['surveyUrlId'])

    if args.operation == _START:
        if not args.survey_id:
            parser.error('--survey_id is required for this operation.')
        start_survey(cs, args.survey_id)
        print 'You can view results for the survey here:'
        print ('https://www.google.com/insights/consumersurveys/view'
               '?survey=%s\n' % args.survey_id)

    if args.operation == _FETCH:
        if not args.survey_id:
            parser.error('--survey_id is required for this operation.')
        get_survey_results(
            cs,
            args.survey_id,
            args.results_file)
        print 'You can also view the survey results here:'
        print ('https://www.google.com/insights/consumersurveys/view'
               '?survey=%s\n' % args.survey_id)

    if args.operation == _SET_RESPONSE_COUNT:
        if not args.survey_id:
            parser.error('--survey_id is required for this operation.')
        update_survey_response_count(cs, args.survey_id, 120)


def get_survey(cs, survey_id):
    return cs.surveys().get(surveyUrlId=survey_id).execute()


def start_survey(cs, survey_id):
    """Sends the survey to the review process and it is then started.

    Args:
        cs: The Consumer Surveys Service used to send the HTTP requests.
        survey_id: The survey id for which we are starting the survey.

    Returns:
        A dictionary containing the survey id of the started survey.
    """
    json_spec = {'state': 'running'}
    return cs.surveys().update(
        surveyUrlId=survey_id, body=json_spec).execute()


def get_survey_results(cs, survey_id, result_file):
    """Writes the survey results into a xls file.

    Args:
        cs: The Consumer survey service used to send the HTTP requests.
        survey_id: The survey id for which we are downloading the
            survey results for.
        result_file: The file name which we write the survey results to.
    """
    f = open(result_file, 'w')
    f.write(cs.results().get_media(surveyUrlId=survey_id).execute())
    print 'Successfully wrote survey %s results to %s\n' % (survey_id,
                                                            result_file)


def create_survey(cs, owner_emails):
    """Creates a new survey using a json object containing necessary
       survey fields.

    Args:
        cs: The consumer survey service used to send the HTTP requests.
        owner_emails: The list of owners that will be in the newly created
            survey.
    Returns:
        A dictionary containing the survey id of the created survey.
    """
    body_def = {
        'title': 'Phone purchase survey',
        'description': 'What phones do people buy and how much do they pay?',
        'owners': owner_emails,
        'wantedResponseCount': 100,
        'audience': {
            'country': 'US',
        },
        'questions': [
            {
                'lowValueLabel': '1',
                'openTextPlaceholder': 'enter amount here',
                'question': 'How much did you pay for your last phone?',
                'singleLineResponse': True,
                'type': 'openNumericQuestion',
                'unitOfMeasurementLabel': '$',
                'unitsPosition': 'before',
            }
        ]
    }
    try:
        survey = cs.surveys().insert(body=body_def).execute()
    except googleapiclient.errors.HttpError, e:
        print 'Error creating the survey: %s\n' % e
        return None
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
    body_def = {'wantedResponseCount': new_response_count}
    return cs.surveys().update(surveyUrlId=survey_id, body=body_def).execute()


def setup_auth(args):
    """Set up and authentication httplib.

    Args:
        args: ArgumentParser with additional command-line flags to pass to
            the OAuth authentication flow.

    Returns:
        An http client library with authentication enabled.
    """
    # Perform OAuth 2.0 authorization.
    if args.robo_email:
        # Service accounts will follow the following authenication.
        client_email = args.robo_email
        with open(args.service_accounts_secrets_file) as f:
            private_key = json.loads(f.read())['private_key']
        credentials = client.SignedJwtAssertionCredentials(client_email,
                                                           private_key,
                                                           scope=SCOPES)
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
