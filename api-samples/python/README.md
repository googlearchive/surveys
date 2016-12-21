## Environment setup

Here are the setup instructions to configure your environment to run the sample code:

### 1. [Activate the Surveys API][1]

### 2. Obtain service account credentials
* Navigate to the [Service accounts page][2] in the Google Developer Console
* Select the project created in step 1.
* Click "Create Service Account"
* Fill in the field for "Service account name".  **Note the Service account ID, which is used in some sample code.**
* Click "Furnish a new private key", and select JSON.
* Click "Create".
* Rename the downloaded JSON file as `account_secret.json` and place in the same directory as the sample code.

### 3. Install the client library

`pip install --upgrade google-api-python-client`

## Notes

* When creating a survey, the owner emails must include both the Service account email address and the email that you use to log into the Google Developer Console.

[1]: https://developers.google.com/surveys/v2/guides/getting-started-guide#activate-the-surveys-api
[2]: https://console.developers.google.com/iam-admin/serviceaccounts/
