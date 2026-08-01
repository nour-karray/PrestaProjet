# Démarrage local d’Ollama

Le pipeline utilise Ollama directement sur Windows, sans Docker.

```powershell
ollama serve
ollama pull qwen2.5:7b-instruct
ollama list
```

Configuration locale :

```env
LOCAL_LLM_URL=http://127.0.0.1:11434
LOCAL_LLM_MODEL=qwen2.5:7b-instruct
LOCAL_LLM_TIMEOUT_SECONDS=300
LOCAL_LLM_MAX_TOKENS=4096
LOCAL_LLM_TEMPERATURE=0
```

Contrôles :

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

L’API applicative protégée est `GET /api/v1/ai/health`. Elle ne retourne aucun
secret. En Docker uniquement, l’URL devient
`http://host.docker.internal:11434`.

