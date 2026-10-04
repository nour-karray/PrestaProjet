package com.trainflow.trainingcase;
import com.trainflow.company.*; import com.trainflow.trainer.Trainer; import jakarta.persistence.*; import java.time.*; import java.util.UUID; import org.hibernate.annotations.JdbcTypeCode; import org.hibernate.type.SqlTypes;
@Entity @Table(name="training_cases")
public class TrainingCase {
 @Id @JdbcTypeCode(SqlTypes.VARCHAR) @Column(columnDefinition="char(36)") private UUID id;
 @Column(nullable=false,unique=true,length=20) private String reference;
 @Column(name="reference_year",nullable=false) private int referenceYear;
 @Column(name="sequence_number",nullable=false) private int sequenceNumber;
 @ManyToOne(fetch=FetchType.LAZY,optional=false) @JoinColumn(name="company_id") private Company company;
 @ManyToOne(fetch=FetchType.LAZY) @JoinColumn(name="primary_contact_id") private CompanyContact primaryContact;
 @ManyToOne(fetch=FetchType.LAZY) @JoinColumn(name="trainer_id") private Trainer trainer;
 @Column(nullable=false,length=250) private String theme; @Column(columnDefinition="text") private String description;
 @Enumerated(EnumType.STRING) @Column(nullable=false,length=40) private TrainingCaseStatus status=TrainingCaseStatus.BROUILLON;
 @Column(name="desired_start_date") private LocalDate desiredStartDate; @Column(name="desired_end_date") private LocalDate desiredEndDate;
 @JdbcTypeCode(SqlTypes.VARCHAR) @Column(name="created_by",nullable=false,columnDefinition="char(36)") private UUID createdBy;
 @Column(name="created_at",nullable=false,updatable=false) private Instant createdAt; @Column(name="updated_at",nullable=false) private Instant updatedAt; @Column(name="closed_at") private Instant closedAt; @Column(name="is_archived",nullable=false) private boolean archived;
 protected TrainingCase(){} public TrainingCase(String reference,int referenceYear,int sequenceNumber,Company company,String theme,UUID createdBy){id=UUID.randomUUID();this.reference=reference;this.referenceYear=referenceYear;this.sequenceNumber=sequenceNumber;this.company=company;this.theme=theme;this.createdBy=createdBy;}
 @PrePersist void insert(){var now=Instant.now();if(id==null)id=UUID.randomUUID();if(createdAt==null)createdAt=now;updatedAt=now;} @PreUpdate void update(){updatedAt=Instant.now();}
 public UUID getId(){return id;} public String getReference(){return reference;} public int getReferenceYear(){return referenceYear;} public int getSequenceNumber(){return sequenceNumber;} public Company getCompany(){return company;} public void setCompany(Company v){company=v;} public CompanyContact getPrimaryContact(){return primaryContact;} public void setPrimaryContact(CompanyContact v){primaryContact=v;} public Trainer getTrainer(){return trainer;} public void setTrainer(Trainer v){trainer=v;} public String getTheme(){return theme;} public void setTheme(String v){theme=v;} public String getDescription(){return description;} public void setDescription(String v){description=v;} public TrainingCaseStatus getStatus(){return status;} public void setStatus(TrainingCaseStatus v){status=v;} public LocalDate getDesiredStartDate(){return desiredStartDate;} public void setDesiredStartDate(LocalDate v){desiredStartDate=v;} public LocalDate getDesiredEndDate(){return desiredEndDate;} public void setDesiredEndDate(LocalDate v){desiredEndDate=v;} public Instant getCreatedAt(){return createdAt;} public Instant getUpdatedAt(){return updatedAt;} public Instant getClosedAt(){return closedAt;} public void setClosedAt(Instant v){closedAt=v;} public boolean isArchived(){return archived;} public void setArchived(boolean v){archived=v;}
}
