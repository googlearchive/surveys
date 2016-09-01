# DEPRECATED - for archival purposes only

In order to use the following library you should do the following..

# One-time OAuth 2 setup.

- If you see the warning "To create an OAuth client ID, you need to set a
  product name in the consent screen.", then you need to go back to the
  Credentials page and click the "OAuth consent screen" tab and fill out the
  necessary information on that page before proceeding.


# Common Errors (and what to do about them)

## ImportError: No module named apiclient.discovery

You need to install the necessary Python modules that are dependencies of this
code.  On most standard Python installations, this is done with 'pip install
google-api-python-client'

## oauth2client.clientsecrets.InvalidClientSecretsError: File not found: "client_secrets.json"

This is an error indicating that the necessary 2-legged OAuth file that
contains your client's secrets cannot be found.

## oauth2client.clientsecrets.InvalidClientSecretsError: Missing property "redirect_uris" in a client type of "web".

You should have chosen the "Other" App Type option when creating your OAuth 2.0
Client ID.

## IOError: [Errno 2] No such file or directory: 'robot_account_secret.json'

This is an error indicating that the necessary OAuth file that
contains the robot client's secrets cannot be found.
