package com.trainflow.auth;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "administrators")
public class Administrator {
    @Id private UUID id;
    @Column(name = "full_name", nullable = false, length = 150) private String fullName;
    @Column(nullable = false, unique = true, length = 320) private String email;
    @Column(name = "password_hash", nullable = false, length = 255) private String passwordHash;
    @Column(name = "is_active", nullable = false) private boolean active;
    @Column(name = "created_at", nullable = false, updatable = false) private Instant createdAt;
    @Column(name = "updated_at", nullable = false) private Instant updatedAt;
    @Column(name = "last_login_at") private Instant lastLoginAt;

    protected Administrator() {}
    public Administrator(String fullName, String email, String passwordHash, boolean active) {
        this.id = UUID.randomUUID(); this.fullName = fullName; this.email = email;
        this.passwordHash = passwordHash; this.active = active;
    }
    @PrePersist void beforeInsert() { Instant now = Instant.now(); if (id == null) id = UUID.randomUUID(); if (createdAt == null) createdAt = now; updatedAt = now; }
    @PreUpdate void beforeUpdate() { updatedAt = Instant.now(); }
    public UUID getId() { return id; }
    public String getFullName() { return fullName; }
    public String getEmail() { return email; }
    public String getPasswordHash() { return passwordHash; }
    public boolean isActive() { return active; }
    public Instant getCreatedAt() { return createdAt; }
    public Instant getLastLoginAt() { return lastLoginAt; }
    public void setLastLoginAt(Instant value) { lastLoginAt = value; }
}
