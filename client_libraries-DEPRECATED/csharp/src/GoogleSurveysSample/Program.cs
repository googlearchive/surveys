/* Copyright 2016 Google Inc. All Rights Reserved.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
*/

/* Command-line tool for interacting with the Google Surveys API.
To run, generate a client secret using https://console.developers.google.com/
under the APIs and Auth Tab for your project. Then download the key.p12 file.

For more instructions on how to obtain the local files necessary for OAuth
authorization, please see https://github.com/google/surveys

Use the following command line arguments.
To create a survey:
-o=create -oe=<email1> -se=<email>
To set the number of desired responses on a survey:
-o=set_num_responses -s=<id> -se=<email>
To start the survey:
-o=start -s=<id> -se=<email>
To download survey results:
-o=fetch -s=<id> -se=<email> -rf=result.xls
To list the list of surveys you are an owner of:
-o=list -se=<email>
*/
using System;
using System.Collections.Generic;
using Google.Apis.Auth.OAuth2;
using Google.Apis.Surveys.v2;
using Google.Apis.Surveys.v2.Data;
using Google.Apis.Services;
using NDesk.Options;
using System.IO;

namespace GoogleSurveysSample
{
    class Program
    {
        // Constants that enumerate the various operations that the client allows.

        // Create a new survey.
        private static string CREATE = "create";

        // Set the desired response count of an existing survey.
        private static string SET_RESPONSE_COUNT = "set_response_count";

        // Start an existing survey.
        private static string START = "start";

        // Get an existing survey.
        private static string GET = "get";

        // Delete an existing survey.
        private static string DELETE = "delete";

        // Fetch the result of an existing survey.
        private static string FETCH = "fetch";

        // List the surveys that this user owns.
        private static string LIST = "list";

        static void Main(string[] args)
        {
            List<String> operations = new List<string>();
            operations.Add(CREATE);
            operations.Add(SET_RESPONSE_COUNT);
            operations.Add(START);
            operations.Add(GET);
            operations.Add(DELETE);
            operations.Add(FETCH);
            operations.Add(LIST);

            bool showHelp = false;
            string serviceAccountEmail = null;
            List<string> owners = new List<string>();
            string resultFile = null;
            string surveyId = null;
            string operation = null;
            var p = new OptionSet() {
                { "o|operation=",
                  "The operation that you want to perform. Possible operations are: " + operations,
                  v => operation = v },
                { "s|survey_id=", "survey id to operate on.",
                  v => surveyId = v },
                { "oe|owner_email=", "List of survey owners' email to use to create surveys.",
                  v => owners.Add(v) },
                { "r|result_file=", "filename to store excel results.",
                  v => resultFile = v },
                { "se|service_account_email=", "Specify a service account email to use for auth.",
                  v => serviceAccountEmail = v },
                { "h|help=",  "show this message and exit",
                  v => showHelp = v != null },
            };
            List<string> extra;
            try
            {
                extra = p.Parse(args);
            }
            catch (OptionException e)
            {
                Console.WriteLine(e.Message);
                Console.WriteLine("Try '--help' for more information.");
                return;
            }

            if (showHelp)
            {
                Console.WriteLine("Create and modify surveys.");
                return;
            }

            if (operation == null || !operations.Contains(operation)) {
                Console.WriteLine("\nMissing or incorrect operation. " +
                    "You must use one of these operations: " + operations);
                return;
            }

            var surveysService = GetServiceAccountCredential();

            if (surveysService == null)
            {
                Console.WriteLine("\nA Survey service was not created.");
                return;
            }

            if (operation == CREATE)
            {
                if (owners == null || owners.Count == 0)
                {
                    Console.WriteLine("\nOwner must be specified when creating a survey.");
                    return;
                }
                Survey survey = CreateSurvey(surveysService, owners);
                Console.WriteLine("Create survey with id: " + survey.SurveyUrlId);
//                survey = UpdateSurveyResponseCount(surveysService, survey.SurveyUrlId, 120);
            }

            if (operation == START)
            {
                if (surveyId == null)
                {
                    Console.WriteLine("\nsurveyId must be specified when starting a survey.");
                    return;
                }
                StartSurvey(surveysService, surveyId);
            }

            if (operation == GET)
            {
                if (surveyId == null)
                {
                    Console.WriteLine("\nsurveyId must be specified when getting a survey.");
                    return;
                }
                Survey survey = GetSurvey(surveysService, surveyId);
                Console.WriteLine("\nSurvey title: " + survey.Title);
            }

            if (operation == DELETE)
            {
                if (surveyId == null)
                {
                    Console.WriteLine("\nsurveyId must be specified when deleting a survey.");
                    return;
                }
                DeleteSurvey(surveysService, surveyId);
                Console.WriteLine("\nDeleted Survey " + surveyId);
            }

            if (operation == SET_RESPONSE_COUNT)
            {
                if (surveyId == null)
                {
                    Console.WriteLine("\nsurveyId must be specified when setting response count.");
                    return;
                }
                UpdateSurveyResponseCount(surveysService, surveyId, 120);
            }

            if (operation == FETCH)
            {
                if (surveyId == null)
                {
                    Console.WriteLine("\nsurveyId must be specified for fetching results.");
                    return;
                }
                if (resultFile == null)
                {
                    resultFile = "results.xls";
                }
                GetSurveyResults(surveysService, surveyId, resultFile);
            }

            if (operation == LIST)
            {
                ListSurveys(surveysService);
            }
        }

        /// <summary>
        /// Creates a new survey using a json object containing necessary survey fields.
        /// </summary>
        /// <param name="surveysService"> The survey service used to send the HTTP requests.</param>
        /// <param name="owners"> The list of owners that will be in the newly created survey.</param>
        /// <returns>
        /// A Survey object containing information about the survey.
        /// </returns>

        private static Survey CreateSurvey(SurveysService surveysService, List<String> owners)
        {

            // [START google_surveys_create]
            List<string> langs = new List<string>();
            langs.Add("en-US");

            SurveyAudience audience = new SurveyAudience()
            {
                Country = "US",
                Languages = langs
            };
            List<SurveyQuestion> questions = new List<SurveyQuestion>();
            SurveyQuestion question = new SurveyQuestion()
            {
                Type = "numericOpenEnded",
                Question = "How much did you pay for your last phone?",
                UnitOfMeasurementLabel = "$",
                SingleLineResponse = true,
                OpenTextPlaceholder = "enter amount here",
            };
            questions.Add(question);

            Survey newSurvey = new Survey()
            {
                Owners = owners,
                Description = "What phones do people buy and how much do they pay?",
                Title = "Phone purchase survey",
                WantedResponseCount = 110,
                Audience = audience,
                Questions = questions,
            };
            Survey survey = surveysService.Surveys.Insert(newSurvey).Execute();
            // [END google_surveys_create]

            return survey;
        }

        /// <summary>
        /// Updates the response count of the survey.
        /// </summary>
        /// <param name="surveysService"> The survey service used to send the HTTP requests.</param>
        /// <param name="surveyId"> The survey id for which we are updating the response count for.</param>
        /// <param name="responseCount">  An integer specifing the new response count for the survey.</param>
        /// <returns>
        /// A Survey object containing information about the survey.
        /// </returns>
        private static Survey UpdateSurveyResponseCount(
            SurveysService surveysService, String surveyId, int responseCount)
        {
            Survey survey = new Survey()
            {
                WantedResponseCount = responseCount,
            };
            Survey updatedSurvey = surveysService.Surveys.Update(survey, surveyId).Execute();
            return updatedSurvey;
        }

        /// <summary>
        /// Sends the survey to the review process and it is then started.
        /// </summary>
        /// <param name="surveysService"> The survey service used to send the HTTP requests.</param>
        /// <param name="surveyId"> The survey id of the survey we are starting.</param>
        /// <returns>
        /// A Survey object containing information about the survey.
        /// </returns>      
        private static Survey StartSurvey(SurveysService surveysService, String surveyId)
        {
            // [START google_surveys_start]
            Survey newSurvey = new Survey()
            {
                State = "running",
            };
            Survey survey = surveysService.Surveys.Update(newSurvey, surveyId).Execute();
            // [END google_surveys_start]

            return survey;
        }

        /// <summary>
        /// Gets information about a survey.
        /// </summary>
        /// <param name="surveysService"> The survey service used to send the HTTP requests.</param>
        /// <param name="surveyId"> The survey id of the survey we are getting.</param>
        /// <returns>
        /// A Survey object containing information about the survey.
        /// </returns>
        private static Survey GetSurvey(SurveysService surveysService, String surveyId)
        {
            // [START google_surveys_get]
            Survey survey = surveysService.Surveys.Get(surveyId).Execute();
            // [END google_surveys_get]

            return survey;
        }

        /// <summary>
        /// Deletes a survey.
        /// </summary>
        /// <param name="surveysService"> The survey service used to send the HTTP requests.</param>
        /// <param name="surveyId"> The survey id of the survey we are deleting.</param>
        private static void DeleteSurvey(SurveysService surveysService, String surveyId)
        {
            // [START google_surveys_delete]
            surveysService.Surveys.Delete(surveyId).Execute();
            // [END google_surveys_delete]
        }

        /// <summary>
        /// Prints the surveys that are owned by the given user.
        /// </summary>
        /// <param name="surveysService"> The survey service used to send the HTTP requests.</param>
        private static void ListSurveys(SurveysService surveysService)
        {
            // [START google_surveys_list]
            var surveyListResponse = surveysService.Surveys.List().Execute();
            // [END google_surveys_list]

            foreach (Survey survey in surveyListResponse.Resources)
            {
                Console.WriteLine(survey.SurveyUrlId);
            }
        }

        /// <summary>
        /// Writes the survey results into a xls file.
        /// </summary>
        /// <param name="surveysService"> The survey service used to send the HTTP requests.</param>
        /// <param name="surveyId"> The survey id for which we are downloading the results for.</param>
        /// <param name="resultFile"> The file name which we write the survey results to.</param>
        private static void GetSurveyResults(
            SurveysService surveysService, String surveyId, String resultFile)
        {
            // [START google_surveys_results]
            FileStream fileSteam = new FileStream(resultFile, FileMode.Create);
            surveysService.Results.Get(surveyId).Download(fileSteam);
            // [END google_surveys_results]
        }

        /// <summary>
        /// Creates a Surveys service that be used to send HTTP requests.
        /// </summary>
        /// <returns>
        /// The survey service used to send the HTTP requests.
        /// </returns>         
        private static SurveysService GetServiceAccountCredential()
        {
            String accountSecretFileName = "account_secret.json";

            // [START google_surveys_auth]
            var scopes = new[] {
                SurveysService.Scope.Surveys,
                SurveysService.Scope.SurveysReadonly,
                SurveysService.Scope.UserinfoEmail };

            GoogleCredential credential;
            using (var stream = new FileStream(accountSecretFileName, FileMode.Open, FileAccess.Read))
            {
                credential = GoogleCredential.FromStream(stream).CreateScoped(scopes);
            }

            var surveysService = new SurveysService(new BaseClientService.Initializer()
            {
                HttpClientInitializer = credential,
            });
            // [END google_surveys_auth]

            return surveysService;
        }
    }
}

