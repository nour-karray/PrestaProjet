package com.trainflow.auth;

import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AdministratorRepository extends JpaRepository<Administrator, UUID> {
    Optional<Administrator> findByEmailIgnoreCase(String email);
}
