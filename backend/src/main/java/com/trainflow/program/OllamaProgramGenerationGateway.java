package com.trainflow.program;

import com.trainflow.ai.OllamaClient;
import com.trainflow.shared.error.ApiError;
import java.util.*;
import java.util.concurrent.Semaphore;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;

@Component
public class OllamaProgramGenerationGateway implements ProgramGenerationGateway {
    private static final Semaphore SINGLE_GENERATION = new Semaphore(1);
    private final OllamaClient client;
    private final String model;
    private final String keepAlive;
    private final int maxTokens;
    private final int contextTokens;

    public OllamaProgramGenerationGateway(OllamaClient client,
            @Value("${trainflow.ai.program-model}") String model,
            @Value("${trainflow.ai.program-keep-alive}") String keepAlive,
            @Value("${trainflow.ai.program-max-tokens}") int maxTokens,
            @Value("${trainflow.ai.program-context-tokens:4096}") int contextTokens) {
        this.client = client; this.model = model; this.keepAlive = keepAlive;
        this.maxTokens = maxTokens; this.contextTokens = contextTokens;
    }

    @Override public Map<String, Object> generate(ProgramGenerationInput input) {
        if (!SINGLE_GENERATION.tryAcquire()) throw new ApiError(HttpStatus.TOO_MANY_REQUESTS, "LLM_BUSY",
                "Une génération de programme est déjà en cours. Réessayez après sa fin.");
        try {
            Map<String,Object> metadata=call(buildGlobalPrompt(input),Math.min(maxTokens,384),globalSchema(),intermediateKeepAlive());
            Map<String,Object> result=new LinkedHashMap<>();
            result.put("title",metadata.get("title"));
            result.put("general_objectives",metadata.get("general_objectives"));
            result.put("prerequisites",metadata.get("prerequisites"));
            result.put("evaluation_method",metadata.get("evaluation_method"));
            result.put("duration_days",input.plannedDaysCount());
            List<Map<String,Object>> generatedDays=new ArrayList<>();
            List<String> previousContent=new ArrayList<>();
            int dayBase=input.totalDurationMinutes()/input.plannedDaysCount();
            int dayRemainder=input.totalDurationMinutes()%input.plannedDaysCount();
            for(int dayNumber=1;dayNumber<=input.plannedDaysCount();dayNumber++){
                String callKeepAlive=dayNumber==input.plannedDaysCount()?keepAlive:intermediateKeepAlive();
                Map<String,Object> generated=call(buildDayPrompt(input,dayNumber,previousContent),
                        Math.min(maxTokens,768),daySchema(),callKeepAlive);
                int dayMinutes=dayBase+(dayNumber<=dayRemainder?1:0);
                Map<String,Object> day=deterministicDay(generated,dayNumber,dayMinutes,previousContent);
                generatedDays.add(day);
            }
            result.put("days",generatedDays);
            return result;
        } finally { SINGLE_GENERATION.release(); }
    }

    String buildGlobalPrompt(ProgramGenerationInput input){return """
            Réponds uniquement avec le JSON imposé par le schéma. Rédige en français professionnel.
            Génère le titre, les objectifs généraux, les prérequis et une méthode d'évaluation concrète.
            Thème: %s
            Public cible: %s
            Objectifs du besoin: %s
            Profil formateur structuré: %s
            N'invente aucune information absente du profil.
            """.formatted(input.theme(),input.targetAudience(),input.objectives(),input.trainer());}

    String buildDayPrompt(ProgramGenerationInput input,int dayNumber,List<String> previous){return """
            Réponds uniquement avec le JSON imposé par le schéma. Rédige en français professionnel.
            Génère uniquement le contenu pédagogique du jour %d sur %d pour le thème %s.
            Public: %s. Objectifs: %s. Niveau attendu: progression adaptée au public.
            Produis 2 à 4 modules, chacun avec 4 à 8 notions métier précises et des méthodes autorisées.
            Contenus déjà générés à ne pas répéter: %s
            Les titres génériques tels que Application des concepts, Révision générale ou Théorie sont interdits.
            """.formatted(dayNumber,input.plannedDaysCount(),input.theme(),input.targetAudience(),
                    input.objectives(),previous.isEmpty()?"aucun":String.join(" | ",previous));}

    private Map<String,Object> deterministicDay(Map<String,Object> generated,int dayNumber,int dayMinutes,List<String> previous){
        Map<String,Object> day=new LinkedHashMap<>();day.put("day_number",dayNumber);day.put("title",generated.get("title"));
        List<?> raw=generated.get("contents") instanceof List<?> list?list:List.of();
        List<Map<String,Object>> contents=new ArrayList<>();int count=raw.size();int base=count==0?0:dayMinutes/count,remainder=count==0?0:dayMinutes%count,index=0;
        for(Object value:raw){if(!(value instanceof Map<?,?> item))continue;int total=base+(index<remainder?1:0),theory=total/2;Map<String,Object> normalized=new LinkedHashMap<>();normalized.put("order_index",++index);normalized.put("title",item.get("title"));normalized.put("concepts",item.get("concepts"));normalized.put("methods",item.get("methods"));normalized.put("theory_minutes",theory);normalized.put("practice_minutes",total-theory);contents.add(normalized);previous.add(compact(item));}
        day.put("contents",contents);return day;
    }

    private String compact(Map<?,?> item){String concepts=item.get("concepts") instanceof List<?> list?list.stream().limit(3).map(String::valueOf).reduce((a,b)->a+", "+b).orElse(""):"";return String.valueOf(item.get("title"))+": "+concepts;}

    private Map<String,Object> globalSchema(){return objectSchema(Map.of(
            "title",stringSchema(3),"general_objectives",stringSchema(10),
            "prerequisites",stringSchema(2),"evaluation_method",stringSchema(5)),
            List.of("title","general_objectives","prerequisites","evaluation_method"));}

    private Map<String,Object> daySchema(){Map<String,Object> method=Map.of("type","string","enum",Arrays.stream(PedagogicalMethod.values()).map(Enum::name).toList());Map<String,Object> item=objectSchema(Map.of(
            "title",stringSchema(3),"concepts",Map.of("type","array","minItems",4,"maxItems",8,"uniqueItems",true,"items",stringSchema(2)),
            "methods",Map.of("type","array","minItems",1,"maxItems",3,"uniqueItems",true,"items",method)),List.of("title","concepts","methods"));return objectSchema(Map.of(
            "title",stringSchema(3),"contents",Map.of("type","array","minItems",2,"maxItems",4,"items",item)),List.of("title","contents"));}

    private Map<String,Object> objectSchema(Map<String,Object> properties,List<String> required){Map<String,Object> schema=new LinkedHashMap<>();schema.put("type","object");schema.put("properties",properties);schema.put("required",required);schema.put("additionalProperties",false);return schema;}
    private Map<String,Object> stringSchema(int minLength){return Map.of("type","string","minLength",minLength);}

    static boolean hasUnresolvedPlaceholder(String prompt){
        if(prompt==null)return false;
        return prompt.contains("{{")||prompt.matches("(?s).*\\{[A-Za-z_][A-Za-z0-9_]*}.*");
    }

    private void ensureNoPlaceholder(String prompt){if(hasUnresolvedPlaceholder(prompt))throw new ApiError(HttpStatus.INTERNAL_SERVER_ERROR,"LLM_PROMPT_INVALID","Le prompt IA contient un placeholder non remplacé.");}

    private String intermediateKeepAlive(){return "0s".equalsIgnoreCase(keepAlive)?"30s":keepAlive;}

    private Map<String,Object> call(String prompt,int tokens,Object schema,String callKeepAlive){
        ensureNoPlaceholder(prompt);
        return client.generateJson(model,prompt,callKeepAlive,tokens,contextTokens,schema);
    }

}
