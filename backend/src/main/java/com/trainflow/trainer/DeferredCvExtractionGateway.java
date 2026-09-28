package com.trainflow.trainer;
import org.springframework.stereotype.Component;
@Component
public class DeferredCvExtractionGateway implements CvExtractionGateway {
 public TrainerCv extract(TrainerCv cv){
  cv.setExtractionStatus("REVIEW_REQUIRED");
  cv.setExtractionErrorCode("AI_MIGRATION_PENDING");
  cv.setExtractionError("L’analyse automatique sera migrée avec le module IA. La vérification manuelle reste disponible.");
  return cv;
 }
}
