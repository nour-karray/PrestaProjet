package com.trainflow.security;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.trainflow.shared.error.ApiError;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class JwtServiceTest {
    private static final String SECRET = "TestOnly-JwtSecret-AtLeast-32-Characters-Long";
    private final JwtService jwt = new JwtService(SECRET, "HS256", 30, 7);

    @Test void accessAndRefreshTokensKeepSubjectAndType() {
        UUID id = UUID.randomUUID();
        assertEquals(id, jwt.decodeAccessToken(jwt.createAccessToken(id)));
        assertEquals(id, jwt.decodeRefreshToken(jwt.createRefreshToken(id)));
    }

    @Test void accessTokenCannotBeUsedAsRefreshToken() {
        ApiError error = assertThrows(ApiError.class, () -> jwt.decodeRefreshToken(jwt.createAccessToken(UUID.randomUUID())));
        assertEquals("INVALID_TOKEN_TYPE", error.getCode());
    }

    @Test void invalidTokenKeepsApiErrorCode() {
        ApiError error = assertThrows(ApiError.class, () -> jwt.decodeAccessToken("invalid-token"));
        assertEquals("INVALID_TOKEN", error.getCode());
    }

    @Test void expiredTokenKeepsApiErrorCode() {
        JwtService expiredJwt = new JwtService(SECRET, "HS256", -1, 7);
        ApiError error = assertThrows(ApiError.class,
                () -> expiredJwt.decodeAccessToken(expiredJwt.createAccessToken(UUID.randomUUID())));
        assertEquals("TOKEN_EXPIRED", error.getCode());
    }

    @Test void unsupportedAlgorithmIsRejectedAtStartup() {
        assertThrows(IllegalStateException.class, () -> new JwtService(SECRET, "HS512", 30, 7));
    }
}
