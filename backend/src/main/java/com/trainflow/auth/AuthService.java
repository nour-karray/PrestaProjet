package com.trainflow.auth;

import com.trainflow.auth.dto.AuthUserResponse;
import com.trainflow.security.JwtService;
import com.trainflow.shared.error.ApiError;
import java.time.Instant;
import java.util.Locale;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthService {
    public record AuthResult(AuthUserResponse administrator, String accessToken, String refreshToken) {}
    private final AdministratorRepository administrators;
    private final PasswordEncoder passwords;
    private final JwtService jwt;
    public AuthService(AdministratorRepository administrators, PasswordEncoder passwords, JwtService jwt) {
        this.administrators = administrators; this.passwords = passwords; this.jwt = jwt;
    }

    @Transactional
    public AuthResult login(String email, String password) {
        Administrator administrator = administrators.findByEmailIgnoreCase(email.strip().toLowerCase(Locale.ROOT))
                .orElseThrow(AuthService::invalidCredentials);
        if (!passwords.matches(password, administrator.getPasswordHash())) throw invalidCredentials();
        requireActive(administrator);
        administrator.setLastLoginAt(Instant.now());
        administrators.saveAndFlush(administrator);
        return tokens(administrator);
    }

    @Transactional(readOnly = true)
    public AuthResult refresh(String refreshToken) {
        UUID id = jwt.decodeRefreshToken(refreshToken);
        Administrator administrator = administrators.findById(id).orElseThrow(() -> new ApiError(
                HttpStatus.UNAUTHORIZED, "ADMINISTRATOR_NOT_FOUND", "Le compte associé à cette session est introuvable."));
        requireActive(administrator);
        return tokens(administrator);
    }

    @Transactional(readOnly = true)
    public AuthUserResponse current(Authentication authentication) {
        final UUID id;
        try { id = UUID.fromString(authentication.getName()); }
        catch (RuntimeException error) { throw new ApiError(HttpStatus.UNAUTHORIZED, "INVALID_TOKEN", "Le jeton d’authentification est invalide."); }
        Administrator administrator = administrators.findById(id).orElseThrow(() -> new ApiError(
                HttpStatus.UNAUTHORIZED, "ADMINISTRATOR_NOT_FOUND", "Le compte associé à cette session est introuvable."));
        requireActive(administrator);
        return response(administrator);
    }

    public void logout() { /* Stateless JWT: logout is completed by deleting both browser cookies. */ }

    private AuthResult tokens(Administrator administrator) {
        return new AuthResult(response(administrator), jwt.createAccessToken(administrator.getId()), jwt.createRefreshToken(administrator.getId()));
    }
    private static AuthUserResponse response(Administrator administrator) {
        return new AuthUserResponse(administrator.getId(), administrator.getFullName(), administrator.getEmail(),
                administrator.isActive(), administrator.getCreatedAt(), administrator.getLastLoginAt());
    }
    private static void requireActive(Administrator administrator) {
        if (!administrator.isActive()) throw new ApiError(HttpStatus.FORBIDDEN, "INACTIVE_ACCOUNT", "Ce compte administrateur est désactivé.");
    }
    private static ApiError invalidCredentials() {
        return new ApiError(HttpStatus.UNAUTHORIZED, "INVALID_CREDENTIALS", "L’adresse email ou le mot de passe est incorrect.");
    }
}
