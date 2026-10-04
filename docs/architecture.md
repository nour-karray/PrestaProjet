# Architecture de TrainFlow AI

```text
React / TypeScript / Vite :5173
              ↓ REST + cookies JWT
Spring Boot / Java 21 :8080
       ├── MySQL 8 + Flyway
       ├── stockage local des CV et documents
       ├── PDFBox
       └── Ollama :11434
             ├── qwen2.5:1.5b (CV)
             └── qwen2.5:3b (programmes)
```

Le backend est un monolithe modulaire organisé sous `com.trainflow` : `auth`,
`company`, `trainer`, `trainingcase`, `trainingneed`, `program`, `pricing`,
`document`, `ai`, `security` et `shared`.

Les contrôleurs portent HTTP, les services appliquent les règles métier, les
repositories assurent la persistance et les DTO préservent les contrats REST.
Les entités JPA ne sont pas exposées directement.

## Données et fichiers

MySQL est l’unique source de vérité. Flyway versionne le schéma et Hibernate le
valide avec `ddl-auto=validate`. Les CV et PDF sont écrits sous `storage/`, hors
Git ; leur métadonnée et leur empreinte restent persistées en base.

## IA

Spring extrait le texte des PDF/DOCX, appelle Ollama et valide le JSON avant
toute persistance. La génération de programme suit la même règle : lecture
courte, appel IA hors transaction, validation stricte, puis transaction courte.
Aucun composant Python n’est requis au runtime.
