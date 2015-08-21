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

  /** Global configuration of OAuth 2.0 scope. */
  private static final ImmutableSet<String> SCOPES = ImmutableSet.of(
    "https://www.googleapis.com/auth/consumersurveys",
    "https://www.googleapis.com/auth/consumersurveys.readonly",
    "https://www.googleapis.com/auth/userinfo.email");

  public static void main (String[] args) throws Exception {
      ArgumentParser parser = ArgumentParsers.newArgumentParser("App")
          .defaultHelp(true)
          .description("Create and modify surveys.");
      parser.addArgument("-o", "--owner_email")
          .nargs("*")
          .help("Specify owners' email to use to create surveys.");
      parser.addArgument("-c", "--completed_survey_id")
          .help("survey id to retrieve excel results for");
      parser.addArgument("-s", "--start_survey_id")
          .help("survey id to start the survey");
      parser.addArgument("-rf", "--result_file")
          .setDefault("results.xls")
          .help("filename to store excel results");
      parser.addArgument("-r", "--robo_email")
          .type(String.class)
          .help("Specify a bot email to use for auth.");

      Namespace ns = null;
      try {
          ns = parser.parseArgs(args);
      } catch (ArgumentParserException e) {
          parser.handleError(e);
          System.exit(1);
      }

      String roboEmail = ns.getString("robo_email");
      List<String> owners = ns.<String> getList("owner_email");
      String completedSurveyId = ns.getString("completed_survey_id");
      String resultFile = ns.getString("result_file");
      String startSurveyId = ns.getString("start_survey_id");

      if (completedSurveyId == null && owners.size() == 0 && startSurveyId == null) {
        System.out.println("\n\nMissing at least one required argument: " +
                           "Please use owner_email or completed_survey_id flags.");
        System.exit(1);
      }

      Consumersurveys cs = getConsumerSurverysService(roboEmail);

      if (owners.size() > 0) {
        Survey survey = createSurvey(cs, owners);
        String surveyId = survey.getSurveyUrlId();
        survey = updateSurveyResponseCount(cs, surveyId, 120);
      }
      if (startSurveyId != null) {
        startSurvey(cs, startSurveyId); 
      }
      if (completedSurveyId != null) {
        getSurveyResults(cs, completedSurveyId, resultFile);
      }
  }

  // Creates a survey and setting the owners on it.
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
      question.setLowValueString("1");
      question.setUnitOfMeasurementLabel("$");
      question.setSingleLineResponse(true);
      question.setOpenTextPlaceholder("enter amount here");
      questions.add(question);
      survey.setQuestions(questions);


      Survey createdSurvey = cs.surveys().insert(survey).execute();
      System.out.println("Create survey with id: " + createdSurvey.getSurveyUrlId());
      return createdSurvey;
  }

  // Updates the response count of a survey.
  private static Survey updateSurveyResponseCount(
      Consumersurveys cs, String surveyId, int responseCount) throws Exception{
    Survey survey = new Survey();
    survey.setWantedResponseCount(responseCount);
    Survey updatedSurvey = cs.surveys().update(surveyId, survey).execute();
    System.out.println("something2: " + updatedSurvey.toPrettyString());
    return updatedSurvey;
  }

  // Sends a survey to ops queue to start.
  private static Survey startSurvey(Consumersurveys cs, String surveyId) throws Exception{
    Survey survey = new Survey();
    survey.setState("running");
    System.out.println("something1: " + survey.toPrettyString());
    Survey updatedSurvey = cs.surveys().update(surveyId, survey).execute();
    System.out.println("something2: " + updatedSurvey.toPrettyString());
    return updatedSurvey;
  }

  // Gets a survey object containing the survey information.
  private static Survey getSurvey(Consumersurveys cs, String surveyId) throws Exception{
    Survey survey = cs.surveys().get(surveyId).execute();
    return survey;
  }

  // Downloads the survey results as xls file.
  private static SurveyResults getSurveyResults(
      Consumersurveys cs,
      String surveyId,
      String resultFile) throws Exception{
    FileOutputStream fop = null;
    File file = new File(resultFile);
    fop = new FileOutputStream(file);

    cs.results().get(surveyId).executeMediaAndDownloadTo(fop);
    SurveyResults results = new SurveyResults();
    return results;
  }

  // Creates a Consumersurveys service too send the HTTP requests.
  private static Consumersurveys getConsumerSurverysService(
      String roboEmail) throws Exception {
    GoogleCredential credential = new GoogleCredential.Builder()
          .setTransport(HTTP_TRANSPORT)
          .setJsonFactory(JSON_FACTORY)
          .setServiceAccountId(roboEmail)
          .setServiceAccountPrivateKeyFromP12File(new File(PRIVATE_KEY))
          .setServiceAccountScopes(SCOPES)
          .build();
    return new Consumersurveys.Builder(HTTP_TRANSPORT, JSON_FACTORY, credential)
        .setApplicationName(APPLICATION_NAME)
        .setHttpRequestInitializer(credential)
        .build();
  }
}
