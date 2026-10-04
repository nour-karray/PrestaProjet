package com.trainflow.ai;

import com.fasterxml.jackson.core.JsonProcessingException;
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
 public Map<String,Object> generateJson(String model,String prompt,String keepAlive,int maxTokens){return generateJson(model,prompt,keepAlive,maxTokens,0);}
 public Map<String,Object> generateJson(String model,String prompt,String keepAlive,int maxTokens,int contextTokens){return generateJson(model,prompt,keepAlive,maxTokens,contextTokens,"json");}
 public Map<String,Object> generateJson(String model,String prompt,String keepAlive,int maxTokens,int contextTokens,Object format){try{
  Map<String,Object> options=new LinkedHashMap<>();options.put("temperature",0);options.put("num_predict",maxTokens);if(contextTokens>0)options.put("num_ctx",contextTokens);
  Map<String,Object> body=new LinkedHashMap<>();body.put("model",model);body.put("prompt",prompt);body.put("stream",false);body.put("format",format);body.put("keep_alive",keepAlive);body.put("options",options);
  JsonNode response=http.post().uri("/api/generate").bodyValue(body).retrieve().bodyToMono(JsonNode.class).block(timeout);
  if(response==null||!response.hasNonNull("response")||response.get("response").asText().isBlank())throw invalid();
  return json.readValue(response.get("response").asText(),new TypeReference<>(){});
 }catch(ApiError e){throw e;}
 catch(JsonProcessingException e){throw new ApiError(HttpStatus.BAD_GATEWAY,"LLM_INVALID_JSON","Ollama a retourné un JSON invalide.");}
 catch(WebClientResponseException.NotFound e){throw new ApiError(HttpStatus.SERVICE_UNAVAILABLE,"LLM_MODEL_NOT_FOUND","Le modèle Ollama configuré n’est pas installé.");}
 catch(Exception e){if(isTimeout(e))throw new ApiError(HttpStatus.GATEWAY_TIMEOUT,"LLM_TIMEOUT","La génération IA a dépassé le délai autorisé.");throw new ApiError(HttpStatus.SERVICE_UNAVAILABLE,"LLM_UNAVAILABLE","Le serveur Ollama est indisponible.");}}
 private boolean isTimeout(Throwable error){for(Throwable current=error;current!=null;current=current.getCause()){String name=current.getClass().getSimpleName().toLowerCase(),message=String.valueOf(current.getMessage()).toLowerCase();if(name.contains("timeout")||message.contains("timeout")||message.contains("timed out"))return true;}return false;}
 private ApiError invalid(){return new ApiError(HttpStatus.BAD_GATEWAY,"LLM_INVALID_RESPONSE","Ollama a retourné une réponse vide ou invalide.");}
}
