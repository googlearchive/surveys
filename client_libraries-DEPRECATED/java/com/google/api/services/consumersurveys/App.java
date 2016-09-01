/**
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

/**
 * Command-line tool for interacting with the Google Consumer Surveys API.
 * For more instructions on how to obtain the local files necessary for OAuth
 * authorization, please see https://github.com/google/consumer-surveys
 * To create a survey:
 * mvn exec:java -D exec.mainClass=com.google.api.services.consumersurveys.App \
 *   -Dexec.args="-o create -oe=<email> -se=<email>"
 * To set the number of desired responses on a survey:
 * mvn exec:java -D exec.mainClass=com.google.api.services.consumersurveys.App \
 *  -Dexec.args="-o set_num_responses -survey_id <id> -se=<email>"
 * To start the survey:
 * mvn exec:java -D exec.mainClass=com.google.api.services.consumersurveys.App \
 *  -Dexec.args="-o start -survey_id <id> -se=<email>"
 * To download survey results:
 * mvn exec:java -D exec.mainClass=com.google.api.services.consumersurveys.App \
 *  -Dexec.args="-o fetch -survey_id <id> -se=<email> --result_file=results.xls"
 */
package com.google.api.services.consumersurveys;

import com.google.api.client.googleapis.auth.oauth2.GoogleCredential;

import org.json.JSONObject;
import org.json.JSONException;
import org.json.JSONArray;


import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.impl.Arguments;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.ArgumentParserException;
import net.sourceforge.argparse4j.inf.Namespace;

import com.google.common.collect.ImmutableSet;

import com.google.api.client.auth.oauth2.Credential;
import com.google.api.client.googleapis.auth.oauth2.GoogleAuthorizationCodeFlow;
import com.google.api.client.googleapis.auth.oauth2.GoogleClientSecrets;
import com.google.api.client.googleapis.javanet.GoogleNetHttpTransport;
import com.google.api.client.googleapis.json.GoogleJsonResponseException;
import com.google.api.client.json.JsonFactory;
import com.google.api.client.json.jackson2.JacksonFactory;
import com.google.api.client.util.store.DataStoreFactory;
import com.google.api.client.util.store.FileDataStoreFactory;

import com.google.api.services.consumersurveys.Consumersurveys;
import com.google.api.services.consumersurveys.model.Survey;
import com.google.api.services.consumersurveys.model.SurveyResults;
import com.google.api.services.consumersurveys.model.SurveyQuestion;
import com.google.api.services.consumersurveys.model.SurveyAudience;


import java.io.IOException;
import java.io.InputStreamReader;
import java.util.Collections;
import java.util.Map;
import java.io.FileOutputStream;

import com.google.api.client.http.HttpRequest;
import com.google.api.client.http.HttpResponse;
import com.google.api.client.http.ByteArrayContent;
import com.google.api.client.http.HttpRequestFactory;
import com.google.api.client.http.HttpTransport;
import com.google.api.client.http.javanet.NetHttpTransport;
import com.google.api.client.http.GenericUrl;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

public class App{


    private static final String APPLICATION_NAME =
        "Consumer Surveys API v2beta-rev20150727-1.20.0";

  private static final String API_BASE_URL = "https://www.googleapis.com/consumersurveys/v2beta/surveys/";

  /** Global configuration for location of private key file. */
  private static final String PRIVATE_KEY = "key.p12";

  /** Global instance of the JSON factory. */
  private static final JsonFactory JSON_FACTORY = JacksonFactory.getDefaultInstance();

  /** Global instance of the HTTP transport. */
  private static final HttpTransport HTTP_TRANSPORT = new NetHttpTransport();

  /** Constants that enumerate the various operations that the client allows. */

  /** Create a new survey. */
  private static final String CREATE = "create";

  /** Set the desired response count of an existing survey. */
  private static final String SET_RESPONSE_COUNT = "set_response_count";

  /** List the surveys that this user owns. */
  private static final String LIST = "list";

  /** Fetch the results of an existing survey. */
  private static final String FETCH = "fetch";

  /** Sends the survey to a review queue. */
  private static final String START = "start";

  /** The list of all the available client options. */
  private static final ImmutableSet<String> OPTIONS = ImmutableSet.of(
    CREATE,
    SET_RESPONSE_COUNT,
    LIST,
    FETCH,
    START);

  /** Global configuration of OAuth 2.0 scope. */
  private static final ImmutableSet<String> SCOPES = ImmutableSet.of(
    "https://www.googleapis.com/auth/consumersurveys",
    "https://www.googleapis.com/auth/consumersurveys.readonly",
    "https://www.googleapis.com/auth/userinfo.email");

  public static void main (String[] args) throws Exception {
      ArgumentParser parser = ArgumentParsers.newArgumentParser("App")
          .defaultHelp(true)
          .description("Create and modify surveys.");
      parser.addArgument("-o", "--option")
          .choices(OPTIONS)
          .help("The operation to perform.");
      parser.addArgument("-oe", "--owner_email")
          .nargs("*")
          .help("Specify owners' email to use to create surveys.");
      parser.addArgument("-s", "--survey_id")
          .help("survey id to start the survey");
      parser.addArgument("-rf", "--result_file")
          .setDefault("results.xls")
          .help("filename to store excel results");
      parser.addArgument("-se", "--service_account_email")
          .type(String.class)
          .help("Specify a bot email to use for auth.");

      Namespace ns = null;
      try {
          ns = parser.parseArgs(args);
      } catch (ArgumentParserException e) {
          parser.handleError(e);
          System.exit(1);
      }

      String option = ns.getString("option");
      String serviceAccountEmail = ns.getString("service_account_email");
      List<String> owners = ns.<String> getList("owner_email");
      String resultFile = ns.getString("result_file");
      String surveyId = ns.getString("survey_id");

      if (serviceAccountEmail == null) {
        System.out.println("\n\nMissing serviceAccountEmail. " +
                           "serviceAccountEmail is necssary for authenication");
        System.exit(1);
      }

      if (option == null) {
        System.out.println("\n\nMissing option. " +
                           "You must use one of these options: " + OPTIONS);
        System.exit(1);
      }

      Consumersurveys cs = getConsumerSurverysService(serviceAccountEmail);

      try {
        if (option.equals(CREATE)) {
          if (owners == null) {
            System.out.println("\n\nMissing owners. " +
                               "You must specify owners to create a survey.");
            System.exit(1);
          }
          Survey survey = createSurvey(cs, owners);
        }
        if (option.equals(START)) {
          if (surveyId == null) {
            System.out.println("\n\nMissing surveyId. " +
                               "You must specify surveyId to start a survey.");
            System.exit(1);
          }
          startSurvey(cs, surveyId); 
        }
        if (option.equals(SET_RESPONSE_COUNT)) {
          if (surveyId == null) {
            System.out.println("\n\nMissing surveyId. " +
                               "You must specify surveyId to set a response count.");
            System.exit(1);
          }
          updateSurveyResponseCount(cs, surveyId, 120);
        }
        if (option.equals(FETCH)) {
          if (surveyId == null) {
            System.out.println("\n\nMissing surveyId. " +
                               "You must specify surveyId to get the results.");
            System.exit(1);
          }
          getSurveyResults(cs, surveyId, resultFile);
        }
        if (option.equals(LIST)) {
          listSurveys(cs);
        }
      } catch (GoogleJsonResponseException e) {
        System.err.println(e.getDetails());
      }
  }

  /**
   * Creates a new survey using a json object containing necessary survey fields.
   * @param cs The Consumer Surveys Service used to send the HTTP requests.
   * @param owners The list of owners that will be in the newly created survey.
   * return A survey object for the survey we created.
   */
  private static Survey createSurvey(
    Consumersurveys cs, List<String> owners) throws Exception {

      // Setting survey properties.
      Survey survey = new Survey();
      survey.setOwners(owners);
      survey.setDescription("What phones do people buy and how much do they pay?");
      survey.setTitle("Phone purchase survey");
      survey.setWantedResponseCount(110);

      // Creating the audience.
      SurveyAudience audience = new SurveyAudience();
      audience.setCountry("US");
      survey.setAudience(audience);

      // Creating a question for the survey.
      List<SurveyQuestion> questions = new ArrayList<SurveyQuestion>();
      SurveyQuestion question = new SurveyQuestion();
      question.setUnitsPosition("before");
      question.setType("openNumericQuestion");
      question.setQuestion("How much did you pay for your last phone?");
      question.setLowValueLabel("1");
      question.setUnitOfMeasurementLabel("$");
      question.setSingleLineResponse(true);
      question.setOpenTextPlaceholder("enter amount here");
      questions.add(question);
      survey.setQuestions(questions);


      Survey createdSurvey = cs.surveys().insert(survey).execute();
      System.out.println("Created survey with id: " + createdSurvey.getSurveyUrlId());
      return createdSurvey;
  }

  /**
   * Updated the response count of the survey.
   * @param cs The Consumer Surveys Service used to send the HTTP requests.
   * @param survey_id The survey id for which we are updating the response count for.
   * @param responseCount An integer specifing the new response count for
   *        the survey.
   * return A survey object for the survey we started.
   */
  private static Survey updateSurveyResponseCount(
      Consumersurveys cs, String surveyId, int responseCount) throws Exception{
    Survey survey = new Survey();
    survey.setWantedResponseCount(responseCount);
    Survey updatedSurvey = cs.surveys().update(surveyId, survey).execute();
    System.out.println(updatedSurvey.toPrettyString());
    return updatedSurvey;
  }

  /**
   * Sends the survey to the review process and it is then started.
   * @param cs The Consumer Surveys Service used to send the HTTP requests.
   * @param survey_id The survey id for which we are starting.
   * return A survey object for the survey we started.
   */
  private static Survey startSurvey(Consumersurveys cs, String surveyId) throws Exception{
    Survey survey = new Survey();
    survey.setState("running");
    Survey updatedSurvey = cs.surveys().update(surveyId, survey).execute();
    System.out.println(updatedSurvey.toPrettyString());
    return updatedSurvey;
  }

  // Gets a survey object containing the survey information
  private static Survey getSurvey(Consumersurveys cs, String surveyId) throws Exception{
    Survey survey = cs.surveys().get(surveyId).execute();
    return survey;
  }

  /**
   * Prints the surveys that are owned by the given user.
   * @param cs The Consumer Surveys Service used to send the HTTP requests.
   */
  private static void listSurveys(Consumersurveys cs) throws Exception{
    
    List<Survey> surveys = cs.surveys().list().execute().getResources();
    for (Survey survey : surveys) {
      System.out.println(survey.getSurveyUrlId());
    }
  }

  /**
   * Prints the surveys that are owned by the given user.
   * @param cs The Consumer Surveys Service used to send the HTTP requests.
   * @param survey_id The survey id for which we are downloading the
   *        survey results for.
   * @param result_file The file name which we write the survey results to.
   */
  private static void getSurveyResults(
      Consumersurveys cs,
      String surveyId,
      String resultFile) throws Exception{
    FileOutputStream fop = null;
    File file = new File(resultFile);
    fop = new FileOutputStream(file);

    cs.results().get(surveyId).executeMediaAndDownloadTo(fop);
  }

  /**
   * Creates a Consumersurveys service to send the HTTP requests.
   * @param serviceAccount The service account we are using for authenication.
   * return A Consumersurveys service for sending HTTP requests.
   */
  private static Consumersurveys getConsumerSurverysService(
      String serviceAccount) throws Exception {
    GoogleCredential credential = new GoogleCredential.Builder()
          .setTransport(HTTP_TRANSPORT)
          .setJsonFactory(JSON_FACTORY)
          .setServiceAccountId(serviceAccount)
          .setServiceAccountPrivateKeyFromP12File(new File(PRIVATE_KEY))
          .setServiceAccountScopes(SCOPES)
          .build();
    return new Consumersurveys.Builder(HTTP_TRANSPORT, JSON_FACTORY, credential)
        .setApplicationName(APPLICATION_NAME)
        .setHttpRequestInitializer(credential)
        .build();
  }
}
