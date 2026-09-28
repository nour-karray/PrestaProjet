package com.trainflow.trainingcase; import jakarta.persistence.*;
@Entity @Table(name="training_case_counters") public class TrainingCaseCounter { @Id private int year; @Column(name="next_value",nullable=false) private int nextValue; protected TrainingCaseCounter(){} public TrainingCaseCounter(int y){year=y;nextValue=2;} public int take(){return nextValue++;} }
