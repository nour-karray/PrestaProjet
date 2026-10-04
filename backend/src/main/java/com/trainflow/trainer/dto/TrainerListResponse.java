package com.trainflow.trainer.dto; import java.util.List;
public record TrainerListResponse(List<TrainerResponse> items,long total,int page,int pageSize) {}
