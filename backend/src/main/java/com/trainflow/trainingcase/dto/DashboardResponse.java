package com.trainflow.trainingcase.dto; import java.util.List; public record DashboardResponse(long activeCount,long cancelledCount,long archivedCount,List<TrainingCaseResponse> recentCases){}
