package com.trainflow.trainingcase;
import jakarta.persistence.*; import java.time.Instant; import java.util.*; import org.hibernate.annotations.JdbcTypeCode; import org.hibernate.type.SqlTypes;
@Entity @Table(name="activity_logs") public class ActivityLog {
 @Id @JdbcTypeCode(SqlTypes.VARCHAR) @Column(columnDefinition="char(36)") private UUID id;
 @JdbcTypeCode(SqlTypes.VARCHAR) @Column(name="administrator_id",columnDefinition="char(36)") private UUID administratorId;
 @JdbcTypeCode(SqlTypes.VARCHAR) @Column(name="training_case_id",columnDefinition="char(36)") private UUID trainingCaseId;
 @Column(nullable=false,length=80) private String action; @Column(name="entity_type",nullable=false,length=80) private String entityType; @JdbcTypeCode(SqlTypes.VARCHAR) @Column(name="entity_id",columnDefinition="char(36)") private UUID entityId;
 @JdbcTypeCode(SqlTypes.JSON) @Column(nullable=false,columnDefinition="json") private Map<String,Object> details=new LinkedHashMap<>(); @Column(name="created_at",nullable=false) private Instant createdAt;
 protected ActivityLog(){} public ActivityLog(UUID admin,UUID caseId,String action,Map<String,Object> details){this(admin,caseId,action,"training_case",caseId,details);} public ActivityLog(UUID admin,UUID caseId,String action,String type,UUID entity,Map<String,Object> details){id=UUID.randomUUID();administratorId=admin;trainingCaseId=caseId;this.action=action;entityType=type;entityId=entity;this.details=details;}
 @PrePersist void insert(){if(id==null)id=UUID.randomUUID();if(createdAt==null)createdAt=Instant.now();} public UUID getId(){return id;} public String getAction(){return action;} public Map<String,Object> getDetails(){return details;} public Instant getCreatedAt(){return createdAt;}
}
