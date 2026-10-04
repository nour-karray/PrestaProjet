# Pipelines IA

## Analyse des CV

Spring Boot valide et stocke le PDF/DOCX, extrait son texte localement, envoie
uniquement le texte utile à `qwen2.5:1.5b`, valide le JSON structuré puis impose
une revue humaine avant la création du formateur. Une panne Ollama conserve le
fichier et permet la saisie manuelle.

## Génération des programmes

Spring construit `ProgramGenerationInput`, appelle `qwen2.5:3b` hors transaction,
parse et valide strictement le JSON, puis persiste le programme, ses journées et
ses modules dans une transaction courte. Une réponse invalide ne crée aucune
donnée partielle.

## Configuration locale

```dotenv
LOCAL_LLM_URL=http://127.0.0.1:11434
CV_LLM_MODEL=qwen2.5:1.5b
CV_LLM_KEEP_ALIVE=30s
LOCAL_LLM_MODEL=qwen2.5:3b
LOCAL_LLM_KEEP_ALIVE=0s
LOCAL_LLM_MAX_TOKENS=4096
LOCAL_LLM_NUM_CTX=8192
LOCAL_LLM_TIMEOUT_SECONDS=600
```

Le modèle programme est déchargé après chaque réponse afin de préserver la RAM.
Les tests live Ollama sont activés explicitement avec
`RUN_OLLAMA_LIVE_TESTS=true`.
