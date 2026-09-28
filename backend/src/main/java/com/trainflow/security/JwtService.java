package com.trainflow.security;

import com.trainflow.shared.error.ApiError;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.util.Date;
import java.util.UUID;
import javax.crypto.SecretKey;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

@Service
public class JwtService {
    public enum TokenType { ACCESS("access"), REFRESH("refresh"); private final String value; TokenType(String value) { this.value = value; } }
    private final SecretKey key;
    private final Duration accessLifetime;
    private final Duration refreshLifetime;

    public JwtService(@Value("${trainflow.jwt.secret}") String secret,
                      @Value("${trainflow.jwt.algorithm:HS256}") String algorithm,
                      @Value("${trainflow.jwt.access-token-expire-minutes:30}") long accessMinutes,
                      @Value("${trainflow.jwt.refresh-token-expire-days:7}") long refreshDays) {
        if (!"HS256".equals(algorithm)) throw new IllegalStateException("JWT_ALGORITHM doit être HS256 pour rester compatible avec FastAPI.");
        if (secret == null || secret.getBytes(StandardCharsets.UTF_8).length < 32) throw new IllegalStateException("JWT_SECRET doit contenir au moins 32 octets.");
        this.key = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        this.accessLifetime = Duration.ofMinutes(accessMinutes);
        this.refreshLifetime = Duration.ofDays(refreshDays);
    }

    public String createAccessToken(UUID administratorId) { return create(administratorId, TokenType.ACCESS, accessLifetime); }
    public String createRefreshToken(UUID administratorId) { return create(administratorId, TokenType.REFRESH, refreshLifetime); }
    public UUID decodeAccessToken(String token) { return decode(token, TokenType.ACCESS); }
    public UUID decodeRefreshToken(String token) { return decode(token, TokenType.REFRESH); }
    public Duration accessLifetime() { return accessLifetime; }
    public Duration refreshLifetime() { return refreshLifetime; }

    private String create(UUID id, TokenType type, Duration lifetime) {
        Instant now = Instant.now();
        return Jwts.builder().subject(id.toString()).claim("type", type.value)
                .issuedAt(Date.from(now)).expiration(Date.from(now.plus(lifetime)))
                .signWith(key, Jwts.SIG.HS256).compact();
    }

    private UUID decode(String token, TokenType expectedType) {
        final Claims claims;
        try {
            claims = Jwts.parser().verifyWith(key).build().parseSignedClaims(token).getPayload();
        } catch (ExpiredJwtException error) {
            throw new ApiError(HttpStatus.UNAUTHORIZED, "TOKEN_EXPIRED", "Votre session a expiré. Veuillez vous reconnecter.");
        } catch (JwtException | IllegalArgumentException error) {
            throw new ApiError(HttpStatus.UNAUTHORIZED, "INVALID_TOKEN", "Le jeton d’authentification est invalide.");
        }
        if (!expectedType.value.equals(claims.get("type", String.class))) {
            throw new ApiError(HttpStatus.UNAUTHORIZED, "INVALID_TOKEN_TYPE", "Le type de jeton d’authentification est invalide.");
        }
        try { return UUID.fromString(claims.getSubject()); }
        catch (RuntimeException error) {
            throw new ApiError(HttpStatus.UNAUTHORIZED, "INVALID_TOKEN", "Le jeton d’authentification est invalide.");
        }
    }
}
