# Développement local

## Prérequis

- JDK 21 et Maven 3.9 ou supérieur ;
- Node.js 20.9 ou supérieur ;
- MySQL 8.x ;
- Ollama avec `qwen2.5:1.5b` et `qwen2.5:3b`.

## Configuration

```powershell
Copy-Item .env.example .env
```

Renseignez localement les variables MySQL, `SPRING_DATASOURCE_*`, `JWT_SECRET`
et les éventuels identifiants E2E. Ne versionnez jamais `.env`. Le compte de
démonstration est désactivé par défaut.

## Installation et démarrage

```powershell
.\setup-local.cmd
.\start-local.cmd
```

Le script démarre Spring Boot et Vite. MySQL et Ollama doivent déjà être
disponibles. Flyway applique les migrations non destructives au démarrage.

Démarrage manuel :

```powershell
cd backend
mvn spring-boot:run

cd ..\frontend
npm install
npm run dev
```

- Frontend : http://localhost:5173
- API : http://localhost:8080
- Santé : http://localhost:8080/health (`{"status":"ok"}`)
- Ollama : http://127.0.0.1:11434

Utilisez `Ctrl+C` dans chaque terminal pour arrêter les services applicatifs.
