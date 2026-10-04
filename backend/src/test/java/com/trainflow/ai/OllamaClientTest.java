package com.trainflow.ai;

import static org.assertj.core.api.Assertions.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.net.httpserver.HttpServer;
import com.trainflow.shared.error.ApiError;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.web.reactive.function.client.WebClient;

class OllamaClientTest {
    private HttpServer server;

    @AfterEach void stop() { if (server != null) server.stop(0); }

    @Test void distinguishesInvalidJson() throws Exception {
        OllamaClient client = client("{\"response\":\"not-json\"}", 0);
        assertThatThrownBy(() -> client.generateJson("model", "prompt", "0s", 10))
                .isInstanceOf(ApiError.class).extracting("code").isEqualTo("LLM_INVALID_JSON");
    }

    @Test void distinguishesEmptyResponse() throws Exception {
        OllamaClient client = client("{\"response\":\"\"}", 0);
        assertThatThrownBy(() -> client.generateJson("model", "prompt", "0s", 10))
                .isInstanceOf(ApiError.class).extracting("code").isEqualTo("LLM_INVALID_RESPONSE");
    }

    @Test void distinguishesTimeout() throws Exception {
        OllamaClient client = client("{\"response\":\"{}\"}", 1500);
        assertThatThrownBy(() -> client.generateJson("model", "prompt", "0s", 10))
                .isInstanceOf(ApiError.class).extracting("code").isEqualTo("LLM_TIMEOUT");
    }

    @Test void distinguishesUnavailableService() throws Exception {
        server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/api/generate", exchange -> {
            byte[] bytes = "unavailable".getBytes(StandardCharsets.UTF_8);
            exchange.sendResponseHeaders(503, bytes.length);
            exchange.getResponseBody().write(bytes);
            exchange.close();
        });
        server.start();
        OllamaClient client = new OllamaClient(WebClient.builder(), new ObjectMapper(),
                "http://127.0.0.1:" + server.getAddress().getPort(), 1);
        assertThatThrownBy(() -> client.generateJson("model", "prompt", "0s", 10))
                .isInstanceOf(ApiError.class).extracting("code").isEqualTo("LLM_UNAVAILABLE");
    }

    private OllamaClient client(String response, long delayMillis) throws Exception {
        server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/api/generate", exchange -> {
            try {
                if (delayMillis > 0) Thread.sleep(delayMillis);
                byte[] bytes = response.getBytes(StandardCharsets.UTF_8);
                exchange.getResponseHeaders().add("Content-Type", "application/json");
                exchange.sendResponseHeaders(200, bytes.length);
                exchange.getResponseBody().write(bytes);
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt();
            } finally { exchange.close(); }
        });
        server.start();
        return new OllamaClient(WebClient.builder(), new ObjectMapper(),
                "http://127.0.0.1:" + server.getAddress().getPort(), 1);
    }
}
