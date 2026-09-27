package com.trainflow.company;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.util.HashSet;
import java.util.Set;

public class ContactUpdateRequest {
    @JsonIgnore private final Set<String> presentFields = new HashSet<>();
    @Size(min = 1, max = 200) private String fullName;
    @Size(max = 320) @Pattern(regexp = "^$|^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", message = "L'adresse email n'est pas valide.") private String email;
    @Size(max = 50) private String phone;
    @Size(max = 150) private String jobTitle;
    private Boolean isPrimary;
    public String getFullName() { return fullName; }
    public void setFullName(String value) { presentFields.add("fullName"); fullName = value; }
    public String getEmail() { return email; }
    public void setEmail(String value) { presentFields.add("email"); email = value; }
    public String getPhone() { return phone; }
    public void setPhone(String value) { presentFields.add("phone"); phone = value; }
    public String getJobTitle() { return jobTitle; }
    public void setJobTitle(String value) { presentFields.add("jobTitle"); jobTitle = value; }
    public Boolean getIsPrimary() { return isPrimary; }
    public void setIsPrimary(Boolean value) { presentFields.add("isPrimary"); isPrimary = value; }
    public boolean has(String field) { return presentFields.contains(field); }
}
