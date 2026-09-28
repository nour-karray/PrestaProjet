package com.trainflow.auth;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.trainflow.security.JwtService;
import com.trainflow.shared.error.ApiError;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.security.crypto.password.PasswordEncoder;

class AuthServiceTest {
    private AdministratorRepository administrators;
    private PasswordEncoder passwords;
    private JwtService jwt;
    private AuthService auth;

    @BeforeEach
    void setUp() {
        administrators = mock(AdministratorRepository.class);
        passwords = mock(PasswordEncoder.class);
        jwt = mock(JwtService.class);
        auth = new AuthService(administrators, passwords, jwt);
    }

    @Test
    void loginNormalizesEmailVerifiesHashAndUpdatesLastLogin() {
        Administrator administrator = new Administrator("Admin Test", "admin@example.test", "$argon2id$existing", true);
        when(administrators.findByEmailIgnoreCase("admin@example.test")).thenReturn(Optional.of(administrator));
        when(passwords.matches("valid-password", administrator.getPasswordHash())).thenReturn(true);
        when(jwt.createAccessToken(administrator.getId())).thenReturn("access.jwt");
        when(jwt.createRefreshToken(administrator.getId())).thenReturn("refresh.jwt");

        AuthService.AuthResult result = auth.login(" ADMIN@EXAMPLE.TEST ", "valid-password");

        assertEquals("access.jwt", result.accessToken());
        assertEquals("refresh.jwt", result.refreshToken());
        assertNotNull(administrator.getLastLoginAt());
        verify(administrators).saveAndFlush(administrator);
    }

    @Test
    void unknownEmailAndWrongPasswordShareTheSameError() {
        when(administrators.findByEmailIgnoreCase("missing@example.test")).thenReturn(Optional.empty());
        ApiError missing = assertThrows(ApiError.class, () -> auth.login("missing@example.test", "wrong"));

        Administrator administrator = new Administrator("Admin Test", "admin@example.test", "$argon2id$existing", true);
        when(administrators.findByEmailIgnoreCase("admin@example.test")).thenReturn(Optional.of(administrator));
        when(passwords.matches("wrong", administrator.getPasswordHash())).thenReturn(false);
        ApiError incorrect = assertThrows(ApiError.class, () -> auth.login("admin@example.test", "wrong"));

        assertEquals("INVALID_CREDENTIALS", missing.getCode());
        assertEquals("INVALID_CREDENTIALS", incorrect.getCode());
    }

    @Test
    void inactiveAccountIsRejectedAfterPasswordVerification() {
        Administrator administrator = new Administrator("Admin Test", "admin@example.test", "$argon2id$existing", false);
        when(administrators.findByEmailIgnoreCase("admin@example.test")).thenReturn(Optional.of(administrator));
        when(passwords.matches("valid-password", administrator.getPasswordHash())).thenReturn(true);

        ApiError error = assertThrows(ApiError.class, () -> auth.login("admin@example.test", "valid-password"));

        assertEquals("INACTIVE_ACCOUNT", error.getCode());
    }
}
