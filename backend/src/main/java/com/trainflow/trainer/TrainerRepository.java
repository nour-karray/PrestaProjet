package com.trainflow.trainer;
import java.util.*; import org.springframework.data.domain.*; import org.springframework.data.jpa.repository.*; import org.springframework.data.repository.query.Param;
public interface TrainerRepository extends JpaRepository<Trainer,UUID> {
 @Query("select t from Trainer t where (:inactive=true or t.active=true) and (:q is null or lower(t.fullName) like lower(concat('%',:q,'%')) or lower(coalesce(t.jobTitle,'')) like lower(concat('%',:q,'%')) or lower(coalesce(t.company,'')) like lower(concat('%',:q,'%')) or lower(coalesce(t.city,'')) like lower(concat('%',:q,'%'))) and (:specialty is null or lower(coalesce(t.jobTitle,'')) like lower(concat('%',:specialty,'%')) or lower(coalesce(t.notes,'')) like lower(concat('%',:specialty,'%'))) ")
 Page<Trainer> search(@Param("q") String q,@Param("specialty") String specialty,@Param("inactive") boolean inactive,Pageable pageable);
}
