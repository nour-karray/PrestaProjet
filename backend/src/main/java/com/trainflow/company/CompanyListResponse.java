package com.trainflow.company;

import java.util.List;

public record CompanyListResponse(List<CompanyListItem> items, long total, int page, int pageSize) {}
