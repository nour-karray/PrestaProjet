package com.trainflow;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.trainflow.shared.config.HealthController;
import com.trainflow.security.CustomUserDetailsService;
import com.trainflow.security.JwtService;
import com.trainflow.security.JwtAuthenticationFilter;
import com.trainflow.security.SecurityConfig;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.context.annotation.Import;

@WebMvcTest(HealthController.class)
@Import({SecurityConfig.class, JwtAuthenticationFilter.class})
class HealthControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean JwtService jwtService;
    @MockitoBean CustomUserDetailsService userDetailsService;

    @Test
    void returnsHealthStatus() throws Exception {
        mockMvc.perform(get("/health"))
            .andExpect(status().isOk())
            .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
            .andExpect(content().json("{\"status\":\"ok\"}"));
    }
}
