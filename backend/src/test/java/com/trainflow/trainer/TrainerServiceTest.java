package com.trainflow.trainer;

import static org.assertj.core.api.Assertions.*; import static org.mockito.ArgumentMatchers.*; import static org.mockito.Mockito.*;
import com.fasterxml.jackson.databind.ObjectMapper; import com.trainflow.shared.error.ApiError; import com.trainflow.trainer.dto.*; import java.math.BigDecimal; import java.util.*; import org.junit.jupiter.api.*; import org.junit.jupiter.api.io.TempDir; import org.mockito.*; import org.springframework.jdbc.core.JdbcTemplate;

class TrainerServiceTest {
 @Mock TrainerRepository trainers; @Mock TrainerCvRepository cvs; @Mock CvExtractionGateway extraction; @Mock JdbcTemplate jdbc; @TempDir java.nio.file.Path temp;
 TrainerService service;
 @BeforeEach void setup(){MockitoAnnotations.openMocks(this);CvStorageService storage=new CvStorageService(temp.toString(),10);service=new TrainerService(trainers,cvs,storage,extraction,new CvTextExtractor(),jdbc,new ObjectMapper());when(cvs.findFirstByTrainerIdOrderByUploadedAtDesc(any())).thenReturn(Optional.empty());when(trainers.save(any())).thenAnswer(i->{Trainer t=i.getArgument(0);t.insert();return t;});}
 @Test void createsAndArchivesTrainer(){TrainerResponse created=service.create(request("Karim Ben Salah"));assertThat(created.fullName()).isEqualTo("Karim Ben Salah");assertThat(created.isActive()).isTrue();when(trainers.findById(created.id())).thenReturn(Optional.of(captureTrainer()));TrainerResponse archived=service.archive(created.id());assertThat(archived.isActive()).isFalse();}
 @Test void rejectsInactiveTrainerAssignment(){Trainer inactive=captureTrainer();inactive.setActive(false);when(trainers.findById(inactive.getId())).thenReturn(Optional.of(inactive));when(jdbc.queryForList(anyString(),any(Object[].class))).thenReturn(List.of(Map.of("id",UUID.randomUUID().toString(),"is_archived",false)));assertThatThrownBy(()->service.assign(UUID.randomUUID(),inactive.getId())).isInstanceOf(ApiError.class).extracting("code").isEqualTo("TRAINER_INACTIVE");}
 @Test void validatesReviewedCvAndAssociatesTrainer(){TrainerCv cv=new TrainerCv("cv.pdf","x.pdf","application/pdf",10,"abc");cv.insert();cv.setExtractionStatus("REVIEW_REQUIRED");when(cvs.findById(cv.getId())).thenReturn(Optional.of(cv));TrainerResponse result=service.validate(cv.getId(),request("Amina Test"));assertThat(result.fullName()).isEqualTo("Amina Test");assertThat(cv.getTrainerId()).isEqualTo(result.id());assertThat(cv.getExtractionStatus()).isEqualTo("VALIDATED");}
 @Test void rejectsCvThatWasNotReviewed(){TrainerCv cv=new TrainerCv("cv.pdf","x.pdf","application/pdf",10,"abc");cv.insert();when(cvs.findById(cv.getId())).thenReturn(Optional.of(cv));assertThatThrownBy(()->service.validate(cv.getId(),request("Amina"))).isInstanceOf(ApiError.class).extracting("code").isEqualTo("CV_NOT_READY");}
 private Trainer captureTrainer(){Trainer t=new Trainer("Karim");t.insert();return t;}
 private TrainerRequest request(String name){return new TrainerRequest(null,null,name,"test@example.com",null,null,null,null,null,null,null,"Formateur",10,new BigDecimal("50"),new BigDecimal("350"),"Tunis","Tunisie",null,null,null);}
}
