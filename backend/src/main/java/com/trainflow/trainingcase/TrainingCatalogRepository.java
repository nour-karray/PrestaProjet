package com.trainflow.trainingcase; import java.util.*; import org.springframework.data.jpa.repository.JpaRepository;
public interface TrainingCatalogRepository extends JpaRepository<TrainingCatalogItem,UUID>{List<TrainingCatalogItem> findByActiveTrueOrderByCategoryAscTitleAsc();}
