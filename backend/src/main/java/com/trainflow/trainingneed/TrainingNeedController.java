package com.trainflow.trainingneed;
import jakarta.validation.Valid; import java.util.UUID; import org.springframework.http.*; import org.springframework.web.bind.annotation.*;
@RestController @RequestMapping("/api/training-cases/{caseId}/need") public class TrainingNeedController {
 private final TrainingNeedService service; public TrainingNeedController(TrainingNeedService s){service=s;}
 @GetMapping TrainingNeedResponse get(@PathVariable UUID caseId){return service.get(caseId);}
 @PostMapping @ResponseStatus(HttpStatus.CREATED) TrainingNeedResponse create(@PathVariable UUID caseId,@Valid @RequestBody TrainingNeedRequest request){return service.create(caseId,request);}
 @PatchMapping TrainingNeedResponse update(@PathVariable UUID caseId,@Valid @RequestBody TrainingNeedRequest request){return service.update(caseId,request);}
 @PostMapping("/validate") TrainingNeedResponse validate(@PathVariable UUID caseId){return service.validate(caseId);}
}
