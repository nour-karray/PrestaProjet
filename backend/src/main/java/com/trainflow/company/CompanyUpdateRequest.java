package com.trainflow.company;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.validation.constraints.Size;
import java.util.HashSet;
import java.util.Set;

public class CompanyUpdateRequest {
    @JsonIgnore private final Set<String> presentFields = new HashSet<>();
    @Size(min = 1, max = 200) private String name;
    @Size(max = 300) private String address;
    @Size(max = 120) private String city;
    @Size(max = 30) private String postalCode;
    @Size(max = 120) private String country;
    @Size(max = 80) private String taxIdentifier;
    @Size(max = 300) private String website;
    private String notes;

    public String getName() { return name; }
    public void setName(String value) { presentFields.add("name"); name = value; }
    public String getAddress() { return address; }
    public void setAddress(String value) { presentFields.add("address"); address = value; }
    public String getCity() { return city; }
    public void setCity(String value) { presentFields.add("city"); city = value; }
    public String getPostalCode() { return postalCode; }
    public void setPostalCode(String value) { presentFields.add("postalCode"); postalCode = value; }
    public String getCountry() { return country; }
    public void setCountry(String value) { presentFields.add("country"); country = value; }
    public String getTaxIdentifier() { return taxIdentifier; }
    public void setTaxIdentifier(String value) { presentFields.add("taxIdentifier"); taxIdentifier = value; }
    public String getWebsite() { return website; }
    public void setWebsite(String value) { presentFields.add("website"); website = value; }
    public String getNotes() { return notes; }
    public void setNotes(String value) { presentFields.add("notes"); notes = value; }
    public boolean has(String field) { return presentFields.contains(field); }
}
