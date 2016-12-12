Instructions for running the sample:

1. Create a service account via the Google Developer Console
  - Go to the [Google Developer Console](https://console.developers.google.com/apis/credentials)
  - Click on "Create credentials", then "Service account key"
  - Select .p12 as key format, and click "Create"
  - Note the private key password
  - Rename the downloaded file as `key.p12` and place it in the same directory
    as `Program.cs`
2. Build project - should generate a file named `GoogleSurveysSample.exe`
3. Run command:
  - **Create survey**: `GoogleSurveysSample.exe -o=create
    -oe=<OWNER_EMAIL>
    -oe=<SERVICE_ACCOUNT_EMAIL>
    -se=<SERVICE_ACCOUNT_EMAIL>`
    - Note that both the survey owner email and service account email need to be
      included for survey creation
  - **Fetch survey results**: `GoogleSurveysSample.exe -o=fetch
    -se=<SERVICE_ACCOUNT_EMAIL>
    -si=<SURVEY_ID>`
