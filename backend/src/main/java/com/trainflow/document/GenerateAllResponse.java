package com.trainflow.document;
import java.util.List;
public record GenerateAllResponse(List<Result> results,boolean allGenerated){public record Result(DocumentType documentType,boolean success,DocumentResponse document,String error){}}
