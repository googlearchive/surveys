Example clients of the Google Consumer Surveys API.

# Contents

- python: Python version of the library resides here.
  - src: Python source code for the example client library.


# Enabling the API in the Google Developer Console

1. [Create or select a project from the Google Developers Console.](https://pantheon.corp.google.com/project "Link to Google Developers Console")

1. Select the Consumer Surveys API from your project dashboard

![Screenshot of selecting the Consumer Surveys API](/../screenshots/screenshots/dev_console_pick_project_and_api.png
"Select the Consumer Surveys API")

1. Enable the Consumer Surveys API in your project

![Screenshot of enabling the Consumer Surveys API](/../screenshots/screenshots/enable_consumer_surveys_api.png
"Enable the Consumer Surveys API")

1. Decide if you want to use an OAuth 2.0 client ID or a service account.  [Refer to the API documentation](https://developers.google.com/console/help/new/?hl=en_US#credentials-access-security-and-identity) for details.

- Generate an OAuth 2.0 client ID to authenticate with the Consumer Surveys API
  1. Select the Credentials menu in your project
 ![Screenshot of selecting Credentials](/../screenshots/screenshots/select_credentials.png
"Select the Credentials menu")

  1. Select the OAuth 2.0 client ID option
 ![Screenshot of selecting OAuth 2.0 client](/../screenshots/screenshots/select_oauth2_credentials.png
"Select the OAuth 2.0 client ID option")

  1. Select the "Other" Application Type for the new Client ID.  This is
     necessary to execute the example clients in this repo.
 ![Screenshot of selecting Other Application Type](/../screenshots/screenshots/create_other_oauth_app_type.png
"Select the 'Other' OAuth Application Type")

  1. After the client has been created, download the JSON file containing the
     OAuth 2.0 client secrets file.
     You will pass this to your client code in order to authenticate with the
     API.
 ![Screenshot of selecting the button to download the OAuth 2.0 credentials](/../screenshots/screenshots/download_json_secret_file.png
"Select the button to download the OAuth 2.0 credentials")

  1. The first time you execute the local client with these credentials, the
     program will open a web browser that will request that you accept the
     various OAuth scope permissions that are required by the client.
 ![Screenshot of the OAuth 2.0 permission screen](/../screenshots/screenshots/local_oauth_permissions_screen.png
"Example local OAuth 2.0 credentials page.")

- Generate Service Account credentials to authenticate with the Consumer Surveys API

  1. Select the Credentials menu in your project
 ![Screenshot of selecting Credentials](/../screenshots/screenshots/select_credentials.png
"Select the Credentials menu")

  1. Select the Service Account option
 ![Screenshot of selecting Service Account](/../screenshots/screenshots/select_service_account_credentials.png
"Select the Service Account option")

  1. Upon creating the Service Account, the UI will download a file containing
     the necessary credentials.  Store this in a safe place (you cannot
     download it again.)  Also make note of the "Email address" of the newly
     created Service Account, you will need to pass that to the example client
     code.
