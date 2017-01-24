Instructions for running the sample:

1. Build project - should generate a file named `GoogleSurveysSample.exe`
2. Run command:
  - **Create survey**: `GoogleSurveysSample.exe -o=create
    -oe=<OWNER_EMAIL>
    -oe=<SERVICE_ACCOUNT_EMAIL>
    - Note that both the survey owner email and service account email need to be
      included for survey creation
  - **Fetch survey results**: `GoogleSurveysSample.exe -o=fetch
    -si=<SURVEY_ID>`
