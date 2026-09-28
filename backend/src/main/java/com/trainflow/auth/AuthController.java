package com.trainflow.auth;

import com.trainflow.auth.dto.AuthUserResponse;
import com.trainflow.auth.dto.LoginRequest;
import com.trainflow.security.JwtService;
import com.trainflow.shared.error.ApiError;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import java.time.Duration;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseCookie;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.CookieValue;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/auth")
public class AuthController {
    public record AuthResponse(AuthUserResponse administrator, String message) {}
    public record MessageResponse(String message) {}
    private final AuthService auth;
    private final JwtService jwt;
    private final boolean secure;
    private final String sameSite;
    public AuthController(AuthService auth, JwtService jwt,
                          @Value("${trainflow.auth-cookie-secure:false}") boolean secure,
                          @Value("${trainflow.auth-cookie-same-site:Lax}") String sameSite) {
        this.auth = auth; this.jwt = jwt; this.secure = secure; this.sameSite = sameSite;
    }

    @PostMapping("/login")
    AuthResponse login(@Valid @RequestBody LoginRequest request, HttpServletResponse response) {
        AuthService.AuthResult result = auth.login(request.email(), request.password());
        setCookies(response, result);
        return new AuthResponse(result.administrator(), "Connexion réussie.");
    }

    @GetMapping("/me") AuthUserResponse me(Authentication authentication) { return auth.current(authentication); }

    @PostMapping("/refresh")
    MessageResponse refresh(@CookieValue(name = "refresh_token", required = false) String refreshToken,
                            HttpServletResponse response) {
        if (refreshToken == null || refreshToken.isBlank()) throw new ApiError(
                HttpStatus.UNAUTHORIZED, "REFRESH_TOKEN_REQUIRED", "Le jeton de renouvellement est absent.");
        AuthService.AuthResult result = auth.refresh(refreshToken);
        setCookies(response, result);
        return new MessageResponse("Session renouvelée.");
    }

    @PostMapping("/logout")
    MessageResponse logout(HttpServletResponse response) {
        auth.logout();
        response.addHeader(HttpHeaders.SET_COOKIE, cookie("access_token", "", Duration.ZERO).toString());
        response.addHeader(HttpHeaders.SET_COOKIE, cookie("refresh_token", "", Duration.ZERO).toString());
        return new MessageResponse("Déconnexion réussie.");
    }

    private void setCookies(HttpServletResponse response, AuthService.AuthResult result) {
        response.addHeader(HttpHeaders.SET_COOKIE, cookie("access_token", result.accessToken(), jwt.accessLifetime()).toString());
        response.addHeader(HttpHeaders.SET_COOKIE, cookie("refresh_token", result.refreshToken(), jwt.refreshLifetime()).toString());
    }
    private ResponseCookie cookie(String name, String value, Duration maxAge) {
        return ResponseCookie.from(name, value).httpOnly(true).secure(secure).sameSite(sameSite).path("/").maxAge(maxAge).build();
    }
}
