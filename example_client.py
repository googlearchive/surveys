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

"""Example script for clients to see how to use the API.

Reads client credential from clients_secrets.json in the current directory,
initiates an OAuth handshake in the user's browser if no valid token is present,
calls the Consumer Surveys API to read the results for a survey, and writes an
Excel file to results.xls in the same directory.

To run, generate a client secret using https://console.developers.google.com/
under the APIs and Auth Tab for your project. Then download the JSON object
and save it as client_secrets.json

Download and install the python Google Oauth Library:
https://code.google.com/p/google-api-python-client/downloads/list

Or install it with PIP:
pip install google-api-python-client

To create a survey:
    ./example_client.py --owner_email <email>


To download survey results:
    ./example_client.py --completed_survey_id <survey_id>
"""

import argparse
import json
import logging
import httplib2

from oauth2client import file as oauth_file
from oauth2client import tools
from oauth2client.client import flow_from_clientsecrets


CLIENT_SECRETS = 'client_secrets.json'
OAUTH2_STORAGE = 'oauth2.dat'
SCOPES = [
    'https://www.googleapis.com/auth/consumersurveys',
    'https://www.googleapis.com/auth/userinfo.email',
]
API_BASE_URL = 'https://www.googleapis.com/consumersurveys/v2beta/surveys/'
API_SPEC_URL = API_BASE_URL + '%s'
API_RESULTS_URL = API_BASE_URL + '%s/results?alt=media'


def check_response(resp):
    """Print out the response headers and assert that it's a 200.

    Args:
        resp: Response headers dictionary.
    """
    print 'Response headers:', resp
    if resp['status'] != 200:
        raise Exception('Bad response status')


def create_survey(auth_http, owner_email):
    """Create an example survey.

    Args:
        auth_http: authenticated http2lib.
        owner_email: email address of owner.

    Returns:
        Id for newly created survey.
    """
    json_spec = {
        'title': 'Phone purchase survey',
        'description': 'What phones do people buy and how much do they pay?',
        'owners': [owner_email],
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
    resp, content = auth_http.request(API_BASE_URL,
                                      method='POST',
                                      body=json.dumps(body_def),
                                      headers={
                                          'content-type': 'application/json'
                                      })
    check_response(resp)
    print 'Response Payload: ', content

    # Extract new survey_id.
    content = json.loads(content)
    return content.get('surveyUrlId')


def update_survey_response_count(auth_http, survey_id, new_response_count):
    """Update the target response count for a survey.

    Args:
        auth_http: authenticated http2lib.
        survey_id: id for the survey.
        new_response_count: desired number of responses.
    """
    json_spec = {'wanted_response_count': new_response_count}
    body_def = {'jsonSpec': json.dumps(json_spec)}
    resp, content = auth_http.request(API_SPEC_URL % survey_id,
                                      method='PUT',
                                      body=json.dumps(body_def),
                                      headers={
                                          'content-type': 'application/json'
                                      })
    check_response(resp)
    print 'Response Payload: ', content


def get_survey_info(auth_http, survey_id):
    """Retrieve survey info and metadata.

    Args:
        auth_http: authenticated http2lib.
        survey_id: id for the survey.
    """
    resp, content = auth_http.request(API_SPEC_URL % survey_id)
    check_response(resp)
    print 'Response Payload: ', content


def get_survey_results(auth_http, survey_id, results_file):
    """Retrieve results for a survey.

    Args:
        auth_http: authenticated http2lib.
        survey_id: id for the survey.
        results_file: file name to strore excel results in.
    """
    resp, content = auth_http.request(API_RESULTS_URL % survey_id)

    check_response(resp)

    with open(results_file, 'wb') as f:
        f.write(content)

    print 'Results written to', results_file


# TODO: Enable this.
def start_survey(auth_http, survey_id):
    """Start a survey.

    Args:
        auth_http: authenticated http2lib.
        survey_id: id for the survey.
    """
    body_def = {'state': 'running'}
    resp, content = auth_http.request(API_SPEC_URL % survey_id,
                                      method='PUT',
                                      body=json.dumps(body_def),
                                      headers={
                                          'content-type': 'application/json'
                                      })
    check_response(resp)
    print 'Response Payload: ', content


def setup_auth(args):
    """Set up and authentication httplib.

    Args:
        args: ArgumentParser with additional command-line flags to pass to
            the OAuth authentication flow.

    Returns:
        An http client library with authentication enabled.
    """
    # Perform OAuth 2.0 authorization.
    flow = flow_from_clientsecrets(CLIENT_SECRETS, scope=SCOPES)
    storage = oauth_file.Storage(OAUTH2_STORAGE)
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(flow, storage, args)

    http = httplib2.Http()
    auth_http = credentials.authorize(http)
    return auth_http


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--owner_email',
                        help='email of the survey owner')
    parser.add_argument('--completed_survey_id',
                        help='survey id to retrieve excel results for')
    parser.add_argument('--results_file',
                        default='results.xls',
                        help='filename to store excel results')

    # Arguments required by tools.run_flow
    parser.add_argument('--logging_level',
                        default='INFO',
                        help='default logging level to use')
    parser.add_argument('--auth_host_name',
                        default='localhost',
                        help='Hostname for redirects during the OAuth flow')
    parser.add_argument('--auth_host_port',
                        default=[8080],
                        help='Port for redirects during the OAuth flow')
    parser.add_argument('--noauth_local_webserver',
                        action='store_true',
                        default=False,
                        help='Run a local webserver to handle redirects')

    args = parser.parse_args()
    auth_http = setup_auth(args)

    if not args.completed_survey_id and not args.owner_email:
        print ('Missing at least one required argument: '
               'Please use owner_email or completed_survey_id flags.')
        return

    if args.completed_survey_id:
        get_survey_results(
            auth_http,
            args.completed_survey_id,
            args.results_file)

    if args.owner_email:
        survey_id = create_survey(auth_http, args.owner_email)
        if survey_id:
            get_survey_info(auth_http, survey_id)
            update_survey_response_count(auth_http, survey_id, 500)
            print 'New Survey Id', survey_id
        else:
            print 'Failed to create survey.'


if __name__ == '__main__':
    main()
