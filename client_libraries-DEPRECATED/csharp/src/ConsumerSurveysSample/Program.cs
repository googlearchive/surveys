/* Copyright 2015 Google Inc. All Rights Reserved.

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

/* Command-line tool for interacting with the Google Consumer Surveys API.
To run, generate a client secret using https://console.developers.google.com/
under the APIs and Auth Tab for your project. Then download the key.p12 file.

For more instructions on how to obtain the local files necessary for OAuth
authorization, please see https://github.com/google/consumer-surveys

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
using System.Security.Cryptography.X509Certificates;
using Google.Apis.Auth.OAuth2;
using Google.Apis.ConsumerSurveys.v2;
using Google.Apis.ConsumerSurveys.v2.Data;
using Google.Apis.Services;
using NDesk.Options;
using System.IO;

namespace ConsumerSurveysSample
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

            if (serviceAccountEmail == null)
            {
                Console.WriteLine("\nserviceAccountEmail must be specified.");
                return;
            }

            var cs = GetServiceAccountCredential(serviceAccountEmail);

            if (cs == null)
            {
                Console.WriteLine("\nA Consumer survey service was not created.");
                return;
            }

            if (operation == CREATE)
            {
                if (owners == null || owners.Count == 0)
                {
                    Console.WriteLine("\nOwner must be specified when creating a survey.");
                    return;
                }
                Survey survey = CreateSurvey(cs, owners);
                Console.WriteLine("Create survey with id: " + survey.SurveyUrlId);
//                survey = UpdateSurveyResponseCount(cs, survey.SurveyUrlId, 120);
            }
            if (operation == START)
            {
                if (surveyId == null)
                {
                    Console.WriteLine("\nsurveyId must be specified when starting a survey.");
                    return;
                }
                StartSurvey(cs, surveyId);
            }
            if (operation == SET_RESPONSE_COUNT)
            {
                if (surveyId == null)
                {
                    Console.WriteLine("\nsurveyId must be specified when setting response count.");
                    return;
                }
                UpdateSurveyResponseCount(cs, surveyId, 120);
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
                GetSurveyResults(cs, surveyId, resultFile);
            }
            if (operation == LIST)
            {
                ListSurveys(cs);
            }
        }

        /// <summary>
        /// Creates a new survey using a json object containing necessary survey fields.
        /// </summary>
        /// <param name="cs"> The consumer survey service used to send the HTTP requests.</param>
        /// <param name="owners"> The list of owners that will be in the newly created survey.</param>
        /// <returns>
        /// A Survey object containing information about the survey.
        /// </returns>

        private static Survey CreateSurvey(ConsumerSurveysService cs, List<String> owners)
        {
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

            Survey survey = new Survey()
            {
                Owners = owners,
                Description = "What phones do people buy and how much do they pay?",
                Title = "Phone purchase survey",
                WantedResponseCount = 110,
                Audience = audience,
                Questions = questions,
            };
            Survey createdSurvey = cs.Surveys.Insert(survey).Execute();
            return createdSurvey;
        }

        /// <summary>
        /// Updates the response count of the survey.
        /// </summary>
        /// <param name="cs"> The consumer survey service used to send the HTTP requests.</param>
        /// <param name="surveyId"> The survey id for which we are updating the response count for.</param>
        /// <param name="responseCount">  An integer specifing the new response count for the survey.</param>
        /// <returns>
        /// A Survey object containing information about the survey.
        /// </returns>
        private static Survey UpdateSurveyResponseCount(
            ConsumerSurveysService cs, String surveyId, int responseCount)
        {
            Survey survey = new Survey()
            {
                WantedResponseCount = responseCount,
            };
            Survey updatedSurvey = cs.Surveys.Update(survey, surveyId).Execute();
            return updatedSurvey;
        }

        /// <summary>
        /// Sends the survey to the review process and it is then started.
        /// </summary>
        /// <param name="cs"> The consumer survey service used to send the HTTP requests.</param>
        /// <param name="surveyId"> The survey id of the survey we are starting.</param>
        /// <returns>
        /// A Survey object containing information about the survey.
        /// </returns>      
        private static Survey StartSurvey(ConsumerSurveysService cs, String surveyId)
        {
            Survey survey = new Survey()
            {
                State = "running",
            };
            Survey updatedSurvey = cs.Surveys.Update(survey, surveyId).Execute();
            return updatedSurvey;
        }

        /// <summary>
        /// Returns the Survey object for tbe specified survey id.
        /// </summary>
        /// <param name="cs"> The consumer survey service used to send the HTTP requests.</param>
        /// <param name="surveyId"> The survey id of the Survey object we need.</param>
        /// <returns>
        /// A Survey object containing information about the survey.
        /// </returns> 
        private static Survey GetSurvey(ConsumerSurveysService cs, String surveyId)
        {
            Survey survey = cs.Surveys.Get(surveyId).Execute();
            return survey;
        }

        /// <summary>
        /// Prints the surveys that are owned by the given user.
        /// </summary>
        /// <param name="cs"> The consumer survey service used to send the HTTP requests.</param>
        private static void ListSurveys(ConsumerSurveysService cs)
        {
            var surveyListResponse = cs.Surveys.List().Execute();
            foreach (Survey survey in surveyListResponse.Resources)
            {
                Console.WriteLine(survey.SurveyUrlId);
            }
        }

        /// <summary>
        /// Writes the survey results into a xls file.
        /// </summary>
        /// <param name="cs"> The consumer survey service used to send the HTTP requests.</param>
        /// <param name="surveyId"> The survey id for which we are downloading the results for.</param>
        /// <param name="resultFile"> The file name which we write the survey results to.</param>
        private static void GetSurveyResults(
            ConsumerSurveysService cs, String surveyId, String resultFile)
        {
            FileStream fileSteam = new FileStream(resultFile, FileMode.Create);
            cs.Results.Get(surveyId).Download(fileSteam);
        }

        /// <summary>
        /// Creates a Consumersurveys service that be used to send HTTP requests.
        /// </summary>
        /// <param name="serviceAccointEmail"> The service account email we are using for 2LO.</param>
        /// <returns>
        /// The consumer survey service used to send the HTTP requests.
        /// </returns>         
        private static ConsumerSurveysService GetServiceAccountCredential(
            String serviceAccountEmail)
        {
            X509Certificate2 certificate;
            try {
                certificate = new X509Certificate2(
                    @".\key.p12", "notasecret", X509KeyStorageFlags.Exportable);
            } catch (Exception e)
            {
                Console.WriteLine("Make sure key.p12 file is in the right location.\n" +
                    e.ToString());
                return null;
            }
            ServiceAccountCredential credential = new ServiceAccountCredential(
                new ServiceAccountCredential.Initializer(serviceAccountEmail)
                {
                    Scopes = new[] {
                        "https://www.googleapis.com/auth/consumersurveys",
                        "https://www.googleapis.com/auth/consumersurveys.readonly",
                        "https://www.googleapis.com/auth/userinfo.email" }
                }.FromCertificate(certificate));
        
            // Creating the consumer surveys service.
            var service = new ConsumerSurveysService(new BaseClientService.Initializer()
            {
                HttpClientInitializer = credential,
            });
            return service;
        }
    }
}

