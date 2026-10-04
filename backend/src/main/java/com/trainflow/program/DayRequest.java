package com.trainflow.program; import jakarta.validation.constraints.Size; public record DayRequest(@Size(max=250)String title){}
