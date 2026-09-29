package com.trainflow.ai;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.*;
import com.trainflow.shared.error.ApiError;
import java.time.Duration;
import java.util.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.*;

@Component
public class OllamaClient {
 private final WebClient http; private final ObjectMapper json; private final Duration timeout;
 public OllamaClient(WebClient.Builder builder,ObjectMapper json,@Value("${trainflow.ai.base-url}")String url,@Value("${trainflow.ai.timeout-seconds:600}")long seconds){http=builder.baseUrl(url).build();this.json=json;timeout=Duration.ofSeconds(seconds);}
 public Map<String,Object> generateJson(String model,String prompt,String keepAlive,int maxTokens){try{Map<String,Object> body=Map.of("model",model,"prompt",prompt,"stream",false,"format","json","keep_alive",keepAlive,"options",Map.of("temperature",0,"num_predict",maxTokens));JsonNode response=http.post().uri("/api/generate").bodyValue(body).retrieve().bodyToMono(JsonNode.class).block(timeout);if(response==null||!response.hasNonNull("response"))throw invalid();String raw=response.get("response").asText();return json.readValue(raw,new TypeReference<>(){});}catch(ApiError e){throw e;}catch(WebClientResponseException.NotFound e){throw new ApiError(HttpStatus.SERVICE_UNAVAILABLE,"LLM_MODEL_NOT_FOUND","Le modèle Ollama configuré n’est pas installé.");}catch(Exception e){throw new ApiError(HttpStatus.SERVICE_UNAVAILABLE,"LLM_UNAVAILABLE","Le serveur Ollama est indisponible.");}}
 private ApiError invalid(){return new ApiError(HttpStatus.BAD_GATEWAY,"LLM_INVALID_RESPONSE","Ollama a retourné une réponse invalide.");}
}
