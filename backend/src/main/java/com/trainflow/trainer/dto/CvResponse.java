package com.trainflow.trainer.dto;
import java.time.Instant; import java.util.*;
public record CvResponse(UUID id,UUID trainerId,String originalFilename,String mimeType,int fileSize,String sha256,Instant uploadedAt,String extractionStatus,String extractionModel,Integer extractionDurationMs,Map<String,Object> parsedJson,String extractionError,String extractionErrorCode) {}
