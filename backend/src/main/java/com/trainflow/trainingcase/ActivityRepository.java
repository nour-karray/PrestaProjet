package com.trainflow.trainingcase; import java.util.*; import org.springframework.data.jpa.repository.JpaRepository;
public interface ActivityRepository extends JpaRepository<ActivityLog,UUID>{List<ActivityLog> findByTrainingCaseIdOrderByCreatedAtDesc(UUID id);}
