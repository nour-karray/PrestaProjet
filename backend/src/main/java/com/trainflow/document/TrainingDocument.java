package com.trainflow.document;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity @Table(name="training_documents", uniqueConstraints=@UniqueConstraint(name="uq_training_documents_case_type",columnNames={"training_case_id","document_type"}))
public class TrainingDocument {
 @Id @JdbcTypeCode(SqlTypes.VARCHAR) @Column(columnDefinition="char(36)") private UUID id;
 @JdbcTypeCode(SqlTypes.VARCHAR) @Column(name="training_case_id",nullable=false,columnDefinition="char(36)") private UUID trainingCaseId;
 @Enumerated(EnumType.STRING) @Column(name="document_type",nullable=false,length=30) private DocumentType documentType;
 @Enumerated(EnumType.STRING) @Column(nullable=false,length=20) private DocumentStatus status=DocumentStatus.PENDING;
 @Column(name="display_name",nullable=false,length=150) private String displayName;
 @Column(name="internal_filename",length=255) private String internalFilename;
 @Column(name="original_filename",length=255) private String originalFilename;
 @Column(name="relative_path",length=500) private String relativePath;
 @Column(name="mime_type",length=100) private String mimeType;
 @Column(name="file_size") private Long fileSize;
 @Column(length=64) private String sha256;
 @JdbcTypeCode(SqlTypes.JSON) @Column(name="snapshot_data",columnDefinition="json") private Map<String,Object> snapshotData;
 @Column(name="generation_error",columnDefinition="text") private String generationError;
 @Column(name="generated_at") private Instant generatedAt;
 @Column(name="created_at",nullable=false) private Instant createdAt;
 @Column(name="updated_at",nullable=false) private Instant updatedAt;
 protected TrainingDocument(){}
 public TrainingDocument(UUID caseId,DocumentType type,String name){id=UUID.randomUUID();trainingCaseId=caseId;documentType=type;displayName=name;}
 @PrePersist void insert(){var n=Instant.now();if(id==null)id=UUID.randomUUID();if(createdAt==null)createdAt=n;updatedAt=n;} @PreUpdate void update(){updatedAt=Instant.now();}
 public UUID getId(){return id;} public UUID getTrainingCaseId(){return trainingCaseId;} public DocumentType getDocumentType(){return documentType;} public DocumentStatus getStatus(){return status;} public void setStatus(DocumentStatus v){status=v;} public String getDisplayName(){return displayName;} public String getInternalFilename(){return internalFilename;} public void setInternalFilename(String v){internalFilename=v;} public String getOriginalFilename(){return originalFilename;} public void setOriginalFilename(String v){originalFilename=v;} public String getRelativePath(){return relativePath;} public void setRelativePath(String v){relativePath=v;} public String getMimeType(){return mimeType;} public void setMimeType(String v){mimeType=v;} public Long getFileSize(){return fileSize;} public void setFileSize(Long v){fileSize=v;} public String getSha256(){return sha256;} public void setSha256(String v){sha256=v;} public Map<String,Object> getSnapshotData(){return snapshotData;} public void setSnapshotData(Map<String,Object> v){snapshotData=v;} public String getGenerationError(){return generationError;} public void setGenerationError(String v){generationError=v;} public Instant getGeneratedAt(){return generatedAt;} public void setGeneratedAt(Instant v){generatedAt=v;} public Instant getCreatedAt(){return createdAt;} public Instant getUpdatedAt(){return updatedAt;}
}
