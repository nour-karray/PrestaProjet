package com.trainflow.program; import jakarta.validation.constraints.*; public record ReturnRequest(@NotBlank@Size(max=2000)String reason){}
