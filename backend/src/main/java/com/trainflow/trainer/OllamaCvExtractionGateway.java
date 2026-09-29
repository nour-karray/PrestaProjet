package com.trainflow.trainer;

import com.trainflow.ai.OllamaClient;
import com.trainflow.shared.error.ApiError;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class OllamaCvExtractionGateway implements CvExtractionGateway {
 private static final String RULES="""
Return JSON only. Never invent missing information; use null or []. Extract: name, email, phone, gsm, location, current_employer, current_position, years_of_experience, specialties, domains, technical_skills, pedagogical_skills, certifications, diplomas, languages, delivered_trainings, tools. Deduplicate arrays. Do not infer birth data or confuse birthplace with location. CV text:\n""";
 private final OllamaClient client; private final String model,keepAlive; private final int maxChars,maxTokens;
 public OllamaCvExtractionGateway(OllamaClient c,@Value("${trainflow.ai.cv-model}")String model,@Value("${trainflow.ai.cv-keep-alive}")String keepAlive,@Value("${trainflow.ai.cv-max-input-chars}")int maxChars,@Value("${trainflow.ai.cv-max-tokens}")int maxTokens){client=c;this.model=model;this.keepAlive=keepAlive;this.maxChars=maxChars;this.maxTokens=maxTokens;}
 public TrainerCv extract(TrainerCv cv){long start=System.nanoTime();try{String text=cv.getRawText();if(text==null||text.isBlank()){cv.setExtractionStatus("REVIEW_REQUIRED");cv.setExtractionErrorCode("TEXT_EXTRACTION_EMPTY");cv.setExtractionError("Le texte du CV est indisponible. La saisie manuelle reste possible.");return cv;}Map<String,Object> parsed=client.generateJson(model,RULES+text.substring(0,Math.min(text.length(),maxChars)),keepAlive,maxTokens);cv.setParsedJson(parsed);cv.setExtractionStatus("REVIEW_REQUIRED");cv.setExtractionModel(model);cv.setExtractionError(null);cv.setExtractionErrorCode(null);return cv;}catch(ApiError error){cv.setExtractionStatus("REVIEW_REQUIRED");cv.setExtractionModel(model);cv.setExtractionErrorCode(error.getCode());cv.setExtractionError(error.getMessage());return cv;}finally{cv.setExtractionDurationMs((int)((System.nanoTime()-start)/1_000_000));}}
}
