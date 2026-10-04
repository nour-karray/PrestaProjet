# Stratégie de test

| Périmètre | Commande |
| --- | --- |
| Backend Spring | `cd backend && mvn test && mvn package` |
| Frontend Vite | `cd frontend && npm run lint && npm test && npm run build` |
| Parcours réel | `cd frontend && npm run test:e2e` |

Le parcours Playwright utilise Spring Boot, MySQL et Ollama réels. Il exige
`E2E_ADMIN_EMAIL` et `E2E_ADMIN_PASSWORD` dans l’environnement local et couvre
le cycle entreprise → contact → formateur/CV → dossier → besoin → programme IA
→ tarification → PDF → clôture → archivage.

Les suites ne doivent jamais embarquer de secret ni modifier une base non dédiée
à leur scénario.
