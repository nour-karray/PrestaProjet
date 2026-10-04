package com.trainflow.trainer;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity @Table(name = "trainers")
public class Trainer {
    @Id @JdbcTypeCode(SqlTypes.VARCHAR) @Column(columnDefinition = "char(36)") private UUID id;
    @Column(name="first_name", length=100) private String firstName;
    @Column(name="last_name", length=100) private String lastName;
    @Column(name="full_name", nullable=false, length=200) private String fullName;
    @Column(length=320) private String email;
    @Column(length=50) private String phone;
    @Column(name="mobile_phone", length=50) private String mobilePhone;
    @Column(name="birth_date", length=50) private String birthDate;
    @Column(name="birth_place", length=150) private String birthPlace;
    @Column(length=300) private String address;
    @Column(length=200) private String company;
    @Column(name="employer_address", length=300) private String employerAddress;
    @Column(name="job_title", length=200) private String jobTitle;
    @Column(name="years_experience") private Integer yearsExperience;
    @Column(name="hourly_rate", precision=12, scale=2) private BigDecimal hourlyRate;
    @Column(name="daily_rate", precision=12, scale=2) private BigDecimal dailyRate;
    @Column(length=120) private String city;
    @Column(length=120) private String country;
    @Column(name="linkedin_url", length=300) private String linkedinUrl;
    @Column(length=300) private String website;
    @Column(columnDefinition="text") private String notes;
    @Column(name="is_active", nullable=false) private boolean active = true;
    @Column(name="created_at", nullable=false, updatable=false) private Instant createdAt;
    @Column(name="updated_at", nullable=false) private Instant updatedAt;

    protected Trainer() {}
    public Trainer(String fullName) { this.id=UUID.randomUUID(); this.fullName=fullName; }
    @PrePersist void insert(){ var now=Instant.now(); if(id==null) id=UUID.randomUUID(); if(createdAt==null) createdAt=now; updatedAt=now; }
    @PreUpdate void updateTime(){ updatedAt=Instant.now(); }
    public UUID getId(){return id;} public String getFirstName(){return firstName;} public void setFirstName(String v){firstName=v;}
    public String getLastName(){return lastName;} public void setLastName(String v){lastName=v;} public String getFullName(){return fullName;} public void setFullName(String v){fullName=v;}
    public String getEmail(){return email;} public void setEmail(String v){email=v;} public String getPhone(){return phone;} public void setPhone(String v){phone=v;}
    public String getMobilePhone(){return mobilePhone;} public void setMobilePhone(String v){mobilePhone=v;} public String getBirthDate(){return birthDate;} public void setBirthDate(String v){birthDate=v;}
    public String getBirthPlace(){return birthPlace;} public void setBirthPlace(String v){birthPlace=v;} public String getAddress(){return address;} public void setAddress(String v){address=v;}
    public String getCompany(){return company;} public void setCompany(String v){company=v;} public String getEmployerAddress(){return employerAddress;} public void setEmployerAddress(String v){employerAddress=v;}
    public String getJobTitle(){return jobTitle;} public void setJobTitle(String v){jobTitle=v;} public Integer getYearsExperience(){return yearsExperience;} public void setYearsExperience(Integer v){yearsExperience=v;}
    public BigDecimal getHourlyRate(){return hourlyRate;} public void setHourlyRate(BigDecimal v){hourlyRate=v;} public BigDecimal getDailyRate(){return dailyRate;} public void setDailyRate(BigDecimal v){dailyRate=v;}
    public String getCity(){return city;} public void setCity(String v){city=v;} public String getCountry(){return country;} public void setCountry(String v){country=v;}
    public String getLinkedinUrl(){return linkedinUrl;} public void setLinkedinUrl(String v){linkedinUrl=v;} public String getWebsite(){return website;} public void setWebsite(String v){website=v;}
    public String getNotes(){return notes;} public void setNotes(String v){notes=v;} public boolean isActive(){return active;} public void setActive(boolean v){active=v;}
    public Instant getCreatedAt(){return createdAt;} public Instant getUpdatedAt(){return updatedAt;}
}
