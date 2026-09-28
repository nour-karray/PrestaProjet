package com.trainflow.trainer;
import java.util.*; import org.springframework.data.domain.*; import org.springframework.data.jpa.repository.JpaRepository;
public interface TrainerCvRepository extends JpaRepository<TrainerCv,UUID>{ Optional<TrainerCv> findBySha256(String hash); Optional<TrainerCv> findFirstByTrainerIdOrderByUploadedAtDesc(UUID trainerId); Page<TrainerCv> findAllByOrderByUploadedAtDesc(Pageable pageable); }
