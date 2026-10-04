package com.trainflow.trainer.dto; import java.util.List;
public record CvListResponse(List<CvResponse> items,long total,int page,int pageSize) {}
