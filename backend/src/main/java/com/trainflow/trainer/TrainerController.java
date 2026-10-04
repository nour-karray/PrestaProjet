package com.trainflow.trainer;
import com.trainflow.trainer.dto.*; import jakarta.validation.Valid; import java.util.*; import org.springframework.core.io.*; import org.springframework.http.*; import org.springframework.web.bind.annotation.*; import org.springframework.web.multipart.MultipartFile;
@RestController @RequestMapping("/api")
public class TrainerController {
 private final TrainerService service; public TrainerController(TrainerService service){this.service=service;}
 @GetMapping("/trainers") TrainerListResponse list(@RequestParam(required=false)String search,@RequestParam(required=false)String specialty,@RequestParam(name="include_inactive",defaultValue="false")boolean inactive,@RequestParam(defaultValue="1")int page,@RequestParam(name="page_size",defaultValue="20")int size){return service.list(search,specialty,inactive,page,size);}
 @PostMapping("/trainers") @ResponseStatus(HttpStatus.CREATED) TrainerResponse create(@Valid @RequestBody TrainerRequest r){return service.create(r);}
 @GetMapping("/trainers/{id}") TrainerResponse get(@PathVariable UUID id){return service.get(id);}
 @PatchMapping("/trainers/{id}") TrainerResponse patch(@PathVariable UUID id,@Valid @RequestBody TrainerPatchRequest r){return service.patch(id,r);}
 @DeleteMapping("/trainers/{id}") TrainerResponse archive(@PathVariable UUID id){return service.archive(id);}
 @GetMapping("/trainers/{id}/cv") ResponseEntity<Resource> trainerCv(@PathVariable UUID id){var cv=service.trainerCv(id);return ResponseEntity.ok().contentType(MediaType.parseMediaType(cv.mime())).header(HttpHeaders.CONTENT_DISPOSITION,"inline; filename=\""+cv.filename().replace("\"","")+"\"").body(new FileSystemResource(cv.path()));}
 @GetMapping("/trainer-cvs") CvListResponse cvs(@RequestParam(defaultValue="1")int page,@RequestParam(name="page_size",defaultValue="20")int size){return service.listCvs(page,size);}
 @PostMapping(value="/trainer-cvs/upload",consumes=MediaType.MULTIPART_FORM_DATA_VALUE) @ResponseStatus(HttpStatus.CREATED) CvResponse upload(@RequestPart("file")MultipartFile file){return service.upload(file);}
 @GetMapping("/trainer-cvs/{id}") CvResponse cv(@PathVariable UUID id){return service.getCv(id);}
 @DeleteMapping("/trainer-cvs/{id}") @ResponseStatus(HttpStatus.NO_CONTENT) void deleteCv(@PathVariable UUID id){service.deleteCv(id);}
 @PostMapping("/trainer-cvs/{id}/extract") CvResponse extract(@PathVariable UUID id){return service.extract(id);}
 @PostMapping("/trainer-cvs/{id}/validate") @ResponseStatus(HttpStatus.CREATED) TrainerResponse validate(@PathVariable UUID id,@Valid @RequestBody TrainerRequest r){return service.validate(id,r);}
 @PostMapping("/training-cases/{caseId}/trainer") Map<String,Object> assign(@PathVariable UUID caseId,@RequestBody TrainerAssignment assignment){return service.assign(caseId,assignment.trainerId());}
}
