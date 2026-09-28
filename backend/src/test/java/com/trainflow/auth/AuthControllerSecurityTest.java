package com.trainflow.auth;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.mockito.Mockito.verify;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.options;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.trainflow.auth.dto.AuthUserResponse;
import com.trainflow.company.CompanyController;
import com.trainflow.company.CompanyService;
import com.trainflow.security.CustomUserDetailsService;
import com.trainflow.security.JwtAuthenticationFilter;
import com.trainflow.security.JwtService;
import com.trainflow.security.SecurityConfig;
import com.trainflow.shared.error.GlobalExceptionHandler;
import java.time.Duration;
import java.time.Instant;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import jakarta.servlet.http.Cookie;
import org.springframework.security.core.userdetails.User;

@WebMvcTest({AuthController.class, CompanyController.class})
@Import({SecurityConfig.class, JwtAuthenticationFilter.class, GlobalExceptionHandler.class})
class AuthControllerSecurityTest {
    @Autowired MockMvc mvc;
    @MockitoBean AuthService auth;
    @MockitoBean JwtService jwt;
    @MockitoBean CustomUserDetailsService users;
    @MockitoBean CompanyService companies;
    AuthUserResponse administrator;

    @BeforeEach void setUp() {
        administrator = new AuthUserResponse(UUID.randomUUID(), "Admin Test", "admin@example.test", true, Instant.now(), Instant.now());
        when(jwt.accessLifetime()).thenReturn(Duration.ofMinutes(30));
        when(jwt.refreshLifetime()).thenReturn(Duration.ofDays(7));
    }

    @Test void loginIsPublicAndSetsHttpOnlyCookiesWithoutTokensInJson() throws Exception {
        when(auth.login("admin@example.test", "TestOnly-Password!42"))
                .thenReturn(new AuthService.AuthResult(administrator, "access.jwt", "refresh.jwt"));
        mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"email\":\" ADMIN@example.test \",\"password\":\"TestOnly-Password!42\"}"))
                .andExpect(status().isOk())
                .andExpect(result -> {
                    var cookies = result.getResponse().getHeaders("Set-Cookie");
                    assertTrue(cookies.stream().anyMatch(cookie -> cookie.contains("access_token=")
                            && cookie.contains("HttpOnly") && cookie.contains("SameSite=Lax")));
                    assertTrue(cookies.stream().anyMatch(cookie -> cookie.contains("refresh_token=")
                            && cookie.contains("HttpOnly") && cookie.contains("SameSite=Lax")));
                })
                .andExpect(jsonPath("$.administrator.email").value("admin@example.test"))
                .andExpect(jsonPath("$.message").value("Connexion réussie."))
                .andExpect(jsonPath("$.access_token").doesNotExist());
    }

    @Test void protectedRoutesUseCompatibleAuthenticationError() throws Exception {
        mvc.perform(get("/api/companies"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.code").value("AUTHENTICATION_REQUIRED"))
                .andExpect(jsonPath("$.details").isEmpty());
        mvc.perform(get("/api/auth/me"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.code").value("AUTHENTICATION_REQUIRED"));
    }

    @Test void refreshRequiresOnlyRefreshCookie() throws Exception {
        mvc.perform(post("/api/auth/refresh"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.code").value("REFRESH_TOKEN_REQUIRED"));
    }

    @Test void authenticatedLogoutClearsBothCookies() throws Exception {
        UUID id = administrator.id();
        when(jwt.decodeAccessToken("valid-access")).thenReturn(id);
        when(users.loadById(id)).thenReturn(User.withUsername(id.toString()).password("").authorities("ADMIN").build());
        mvc.perform(post("/api/auth/logout").cookie(new Cookie("access_token", "valid-access")))
                .andExpect(status().isOk())
                .andExpect(result -> {
                    var cookies = result.getResponse().getHeaders("Set-Cookie");
                    assertTrue(cookies.stream().anyMatch(cookie -> cookie.contains("access_token=") && cookie.contains("Max-Age=0")));
                    assertTrue(cookies.stream().anyMatch(cookie -> cookie.contains("refresh_token=") && cookie.contains("Max-Age=0")));
                })
                .andExpect(jsonPath("$.message").value("Déconnexion réussie."));
        verify(auth).logout();
    }

    @Test void corsAllowsOnlyTheConfiguredFrontendWithCredentials() throws Exception {
        mvc.perform(options("/api/companies")
                        .header("Origin", "http://localhost:3000")
                        .header("Access-Control-Request-Method", "GET"))
                .andExpect(status().isOk())
                .andExpect(header().string("Access-Control-Allow-Origin", "http://localhost:3000"))
                .andExpect(header().string("Access-Control-Allow-Credentials", "true"));

        mvc.perform(options("/api/companies")
                        .header("Origin", "https://untrusted.example")
                        .header("Access-Control-Request-Method", "GET"))
                .andExpect(status().isForbidden())
                .andExpect(header().doesNotExist("Access-Control-Allow-Origin"));
    }
}
