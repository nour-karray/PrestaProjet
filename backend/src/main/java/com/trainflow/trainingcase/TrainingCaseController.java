package com.trainflow.trainingcase;
import com.trainflow.trainingcase.dto.*; import jakarta.validation.Valid; import java.time.LocalDate; import java.util.*; import org.springframework.http.*; import org.springframework.web.bind.annotation.*;
@RestController @RequestMapping("/api") public class TrainingCaseController {
 private final TrainingCaseService service; public TrainingCaseController(TrainingCaseService s){service=s;}
 @GetMapping("/training-cases") TrainingCaseListResponse list(@RequestParam(required=false)String reference,@RequestParam(name="company_id",required=false)UUID companyId,@RequestParam(required=false)String theme,@RequestParam(required=false)TrainingCaseStatus status,@RequestParam(name="created_from",required=false)LocalDate createdFrom,@RequestParam(name="created_to",required=false)LocalDate createdTo,@RequestParam(name="desired_start_from",required=false)LocalDate startFrom,@RequestParam(name="desired_start_to",required=false)LocalDate startTo,@RequestParam(name="include_archived",defaultValue="false")boolean archived,@RequestParam(defaultValue="1")int page,@RequestParam(name="page_size",defaultValue="10")int size,@RequestParam(name="sort_by",defaultValue="created_at")String sortBy,@RequestParam(name="sort_order",defaultValue="desc")String order){String field=Map.of("created_at","createdAt","updated_at","updatedAt","reference","reference").getOrDefault(sortBy,sortBy);return service.list(reference,companyId,theme,status,createdFrom,createdTo,startFrom,startTo,archived,page,size,field,order);}
 @PostMapping("/training-cases") @ResponseStatus(HttpStatus.CREATED) TrainingCaseResponse create(@Valid @RequestBody TrainingCaseRequest r){return service.create(r);}
 @GetMapping("/training-cases/{id}") TrainingCaseResponse get(@PathVariable UUID id){return service.get(id);}
 @PatchMapping("/training-cases/{id}") TrainingCaseResponse patch(@PathVariable UUID id,@Valid @RequestBody TrainingCasePatchRequest r){return service.patch(id,r);}
 @PostMapping("/training-cases/{id}/change-status") TrainingCaseResponse change(@PathVariable UUID id,@Valid @RequestBody StatusChangeRequest r){return service.change(id,r.status());}
 @PostMapping("/training-cases/{id}/cancel") TrainingCaseResponse cancel(@PathVariable UUID id){return service.cancel(id);}
 @PostMapping("/training-cases/{id}/close") TrainingCaseResponse close(@PathVariable UUID id){return service.close(id);}
 @PostMapping("/training-cases/{id}/archive") TrainingCaseResponse archive(@PathVariable UUID id){return service.archive(id);}
 @GetMapping("/training-cases/{id}/activity") List<ActivityResponse> activity(@PathVariable UUID id){return service.activity(id);}
 @GetMapping("/dashboard") DashboardResponse dashboard(){return service.dashboard();}
 @GetMapping("/training-catalog") List<CatalogItemResponse> catalog(){return service.catalog();}
}
