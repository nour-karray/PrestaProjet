package com.trainflow.program;

import static org.assertj.core.api.Assertions.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.trainflow.ai.OllamaClient;
import java.time.Duration;
import java.util.*;
import java.util.stream.Stream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import org.springframework.web.reactive.function.client.WebClient;

@EnabledIfEnvironmentVariable(named="RUN_OLLAMA_LIVE_TESTS",matches="true")
class OllamaProgramGenerationLiveTest {
    @ParameterizedTest(name="{0}") @MethodSource("needs")
    void generatesSchemaCompliantProgram(String theme,String audience,String objectives) {
        OllamaClient client=new OllamaClient(WebClient.builder(),new ObjectMapper(),"http://127.0.0.1:11434",300);
        OllamaProgramGenerationGateway gateway=new OllamaProgramGenerationGateway(client,"qwen2.5:3b","0s",2048,4096);
        ProgramGenerationInput input=new ProgramGenerationInput(UUID.randomUUID(),theme,audience,objectives,2,240,
                new ProgramGenerationInput.TrainerProfile("Amina",List.of(),List.of(),null,List.of()));
        long start=System.nanoTime();Map<String,Object> raw=gateway.generate(input);ValidatedProgramDraft validated=new ProgramDraftValidator().validate(raw,input);
        long millis=Duration.ofNanos(System.nanoTime()-start).toMillis();
        assertThat(validated.days()).hasSize(2);
        assertThat(validated.days()).allSatisfy(day->{assertThat(day.items()).hasSizeBetween(2,4);assertThat(day.items()).allSatisfy(item->{assertThat(item.content().lines().toList()).hasSizeBetween(4,8);assertThat(item.methods()).isNotEmpty();});});
        List<String> titles=validated.days().stream().flatMap(day->day.items().stream()).map(item->normalize(item.title())).toList();
        assertThat(new HashSet<>(titles)).hasSameSizeAs(titles);
        assertThat(raw.toString()).doesNotContain("PLACEHOLDER_","{theme}","{{");
        System.out.printf(Locale.ROOT,"OLLAMA_LIVE theme=%s elapsed_ms=%d days=%d%n",theme,millis,validated.days().size());
    }

    static Stream<Arguments> needs(){return Stream.of(
            Arguments.of("Cybersécurité","Employés débutants","Reconnaître le phishing et protéger les accès"),
            Arguments.of("Excel","Analystes intermédiaires","Analyser des données avec tableaux croisés et fonctions avancées"),
            Arguments.of("Management","Managers expérimentés","Diagnostiquer et résoudre des situations managériales complexes"));}
    private String normalize(String value){return value.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9à-ÿ]+"," ").trim();}
}
