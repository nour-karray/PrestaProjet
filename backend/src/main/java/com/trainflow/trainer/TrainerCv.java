package com.trainflow.trainer;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity @Table(name="trainer_cvs")
public class TrainerCv {
    @Id @JdbcTypeCode(SqlTypes.VARCHAR) @Column(columnDefinition="char(36)") private UUID id;
    @JdbcTypeCode(SqlTypes.VARCHAR) @Column(name="trainer_id", columnDefinition="char(36)") private UUID trainerId;
    @Column(name="original_filename", nullable=false) private String originalFilename;
    @Column(name="storage_filename", nullable=false, unique=true) private String storageFilename;
    @Column(name="mime_type", nullable=false, length=100) private String mimeType;
    @Column(name="file_size", nullable=false) private int fileSize;
    @Column(nullable=false, unique=true, length=64) private String sha256;
    @Column(name="uploaded_at", nullable=false) private Instant uploadedAt;
    @Column(name="extraction_status", nullable=false, length=32) private String extractionStatus="UPLOADED";
    @Column(name="extraction_model", length=120) private String extractionModel;
    @Column(name="extraction_duration_ms") private Integer extractionDurationMs;
    @Column(name="raw_text", columnDefinition="longtext") private String rawText;
    @JdbcTypeCode(SqlTypes.JSON) @Column(name="parsed_json", columnDefinition="json") private Map<String,Object> parsedJson;
    @Column(name="extraction_error", columnDefinition="text") private String extractionError;
    @Column(name="extraction_error_code", length=64) private String extractionErrorCode;
    protected TrainerCv() {}
    public TrainerCv(String original, String stored, String mime, int size, String hash){id=UUID.randomUUID();originalFilename=original;storageFilename=stored;mimeType=mime;fileSize=size;sha256=hash;}
    @PrePersist void insert(){if(id==null)id=UUID.randomUUID();if(uploadedAt==null)uploadedAt=Instant.now();}
    public UUID getId(){return id;} public UUID getTrainerId(){return trainerId;} public void setTrainerId(UUID v){trainerId=v;} public String getOriginalFilename(){return originalFilename;}
    public String getStorageFilename(){return storageFilename;} public String getMimeType(){return mimeType;} public int getFileSize(){return fileSize;} public String getSha256(){return sha256;}
    public Instant getUploadedAt(){return uploadedAt;} public String getExtractionStatus(){return extractionStatus;} public void setExtractionStatus(String v){extractionStatus=v;}
    public String getExtractionModel(){return extractionModel;} public void setExtractionModel(String v){extractionModel=v;} public Integer getExtractionDurationMs(){return extractionDurationMs;} public void setExtractionDurationMs(Integer v){extractionDurationMs=v;}
    public String getRawText(){return rawText;} public void setRawText(String v){rawText=v;} public Map<String,Object> getParsedJson(){return parsedJson;} public void setParsedJson(Map<String,Object> v){parsedJson=v;}
    public String getExtractionError(){return extractionError;} public void setExtractionError(String v){extractionError=v;} public String getExtractionErrorCode(){return extractionErrorCode;} public void setExtractionErrorCode(String v){extractionErrorCode=v;}
}
