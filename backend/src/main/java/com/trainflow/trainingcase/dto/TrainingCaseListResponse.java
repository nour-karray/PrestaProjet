package com.trainflow.trainingcase.dto; import java.util.List; public record TrainingCaseListResponse(List<TrainingCaseResponse> items,long total,int page,int pageSize){}
