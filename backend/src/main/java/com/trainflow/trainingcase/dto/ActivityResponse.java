package com.trainflow.trainingcase.dto; import java.time.Instant; import java.util.*; public record ActivityResponse(UUID id,String action,Map<String,Object> details,Instant createdAt){}
