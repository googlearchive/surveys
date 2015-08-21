/*
 * Copyright 2015 Google Inc. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
using System;
using System.Collections.Generic;
using System.Security.Cryptography.X509Certificates;
using Google.Apis.Auth.OAuth2;
using Google.Apis.Consumersurveys.v2beta;
using Google.Apis.Consumersurveys.v2beta.Data;
using Google.Apis.Services;
using NDesk.Options;
using System.IO;

namespace ConsumerSurveysSample
{
    class Program
    {
        static void Main(string[] args)
        {
            bool showHelp = false;
            String serviceAccountEmail = null;
            List<String> owners = new List<string>();
            String completedSurveyId = null;
            String resultFile = null;
            String startSurveyId = null;
            var p = new OptionSet() {
                { "o|owner_email=", "Specify owners' email to use to create surveys.",
                  v => owners.Add(v) },
                { "c|completed_survey_id=", "survey id to retrieve excel results for.",
                  v => completedSurveyId = v },
                { "s|start_survey_id=", "survey id to start the survey.",
                  v => startSurveyId = v },
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

            if (completedSurveyId == null && owners.Count == 0 && startSurveyId == null)
            {
                Console.WriteLine("\n\nMissing at least one required argument: " +
                                   "Please use owner_email or completed_survey_id flags.");
                return;
            }
            var cs = GetServiceAccountCredential(serviceAccountEmail);

            if (owners != null && owners.Count > 0)
            {
                Survey survey = CreateSurvey(cs, owners);
                String surveyId = survey.SurveyUrlId;
                Console.WriteLine("Create survey with id: " + surveyId);
                survey = UpdateSurveyResponseCount(cs, surveyId, 120);
            }
            if (startSurveyId != null)
            {
                StartSurvey(cs, startSurveyId);
            }
            if (completedSurveyId != null)
            {
                if (resultFile == null)
                {
                    resultFile = "results.xls";
                }
                GetSurveyResults(cs, completedSurveyId, resultFile);
            }
        }

        // Creates a survey using ConsumersurveyService and sets the owners.
        private static Survey CreateSurvey(ConsumersurveysService cs, List<String> owners)
        {
            SurveyAudience audience = new SurveyAudience()
            {
                Country = "US"
            };
            List<SurveyQuestion> questions = new List<SurveyQuestion>();
            SurveyQuestion question = new SurveyQuestion()
            {
                UnitsPosition = "before",
                Type = "openNumericQuestion",
                Question = "How much did you pay for your last phone?",
                //LowValueString = "1",
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

        // Updates the response count of the survey.
        private static Survey UpdateSurveyResponseCount(ConsumersurveysService cs, String surveyId, int responseCount)
        {
            Survey survey = new Survey()
            {
                WantedResponseCount = responseCount,
            };
            Survey updatedSurvey = cs.Surveys.Update(survey, surveyId).Execute();
            Console.WriteLine("something2: " + updatedSurvey.JsonSpec);
            return updatedSurvey;
        }

        // Sends the survey to ops queue to start.
        private static Survey StartSurvey(ConsumersurveysService cs, String surveyId)
        {
            Survey survey = new Survey()
            {
                State = "running",
            };
            Survey updatedSurvey = cs.Surveys.Update(survey, surveyId).Execute();
            return updatedSurvey;
        }

        // Returns a survey given a survey id.
        private static Survey GetSurvey(ConsumersurveysService cs, String surveyId)
        {
            Survey survey = cs.Surveys.Get(surveyId).Execute();
            Console.WriteLine(survey.JsonSpec);
            return survey;
        }

        // Downloads the xls file containing the survey results.
        private static void GetSurveyResults(ConsumersurveysService cs, String surveyId, String resultFile)
        {
            FileStream fileSteam = new FileStream(resultFile, FileMode.Create);
            cs.Results.Get(surveyId).Download(fileSteam);
        }

        // Creates a Consumersurveys service that be used to send HTTP requests.
        private static ConsumersurveysService GetServiceAccountCredential(String serviceAccountEmail)
        {
            var certificate = new X509Certificate2(@".\key.p12", "notasecret", X509KeyStorageFlags.Exportable);

            ServiceAccountCredential credential = new ServiceAccountCredential(
                new ServiceAccountCredential.Initializer(serviceAccountEmail)
                {
                    Scopes = new[] {
                        "https://www.googleapis.com/auth/consumersurveys",
                        "https://www.googleapis.com/auth/consumersurveys.readonly",
                        "https://www.googleapis.com/auth/userinfo.email" }
                }.FromCertificate(certificate));
        
            // Creating the consumer surveys service.
            var service = new ConsumersurveysService(new BaseClientService.Initializer()
            {
                HttpClientInitializer = credential,
            });
            return service;
        }
    }
}
