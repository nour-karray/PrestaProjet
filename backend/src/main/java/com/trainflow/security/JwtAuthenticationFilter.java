package com.trainflow.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.trainflow.shared.error.ApiError;
import com.trainflow.shared.error.ApiErrorResponse;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.Arrays;
import java.util.Optional;
import org.springframework.http.MediaType;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {
    private final JwtService jwt;
    private final CustomUserDetailsService users;
    private final ObjectMapper objectMapper;
    public JwtAuthenticationFilter(JwtService jwt, CustomUserDetailsService users, ObjectMapper objectMapper) {
        this.jwt = jwt; this.users = users; this.objectMapper = objectMapper;
    }
    @Override protected boolean shouldNotFilter(HttpServletRequest request) {
        String path = request.getRequestURI();
        return path.equals("/health") || path.equals("/api/auth/login") || path.equals("/api/auth/refresh");
    }
    @Override protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        Optional<String> token = cookie(request, "access_token");
        if (token.isEmpty()) { chain.doFilter(request, response); return; }
        try {
            UserDetails user = users.loadById(jwt.decodeAccessToken(token.get()));
            if (!user.isEnabled()) throw new ApiError(org.springframework.http.HttpStatus.FORBIDDEN, "INACTIVE_ACCOUNT", "Ce compte administrateur est désactivé.");
            SecurityContextHolder.getContext().setAuthentication(
                    new UsernamePasswordAuthenticationToken(user, null, user.getAuthorities()));
            chain.doFilter(request, response);
        } catch (ApiError error) {
            write(response, error);
        } catch (UsernameNotFoundException error) {
            write(response, new ApiError(org.springframework.http.HttpStatus.UNAUTHORIZED, "ADMINISTRATOR_NOT_FOUND", "Le compte associé à cette session est introuvable."));
        }
    }
    private Optional<String> cookie(HttpServletRequest request, String name) {
        if (request.getCookies() == null) return Optional.empty();
        return Arrays.stream(request.getCookies()).filter(cookie -> name.equals(cookie.getName())).map(Cookie::getValue).findFirst();
    }
    private void write(HttpServletResponse response, ApiError error) throws IOException {
        response.setStatus(error.getStatus().value()); response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        objectMapper.writeValue(response.getWriter(), new ApiErrorResponse(error.getCode(), error.getMessage(), error.getDetails()));
    }
}
