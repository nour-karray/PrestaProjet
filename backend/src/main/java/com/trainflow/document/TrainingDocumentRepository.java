package com.trainflow.document;
import java.util.*; import org.springframework.data.jpa.repository.JpaRepository;
public interface TrainingDocumentRepository extends JpaRepository<TrainingDocument,UUID>{List<TrainingDocument> findByTrainingCaseIdOrderByDocumentType(UUID caseId);Optional<TrainingDocument> findByTrainingCaseIdAndDocumentType(UUID caseId,DocumentType type);}
