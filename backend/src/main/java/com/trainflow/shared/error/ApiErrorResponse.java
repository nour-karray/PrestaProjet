package com.trainflow.shared.error;

public record ApiErrorResponse(String code, String message, Object details) {}
