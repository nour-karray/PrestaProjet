# Correction ergonomique du workflow des dossiers

## Diagnostic

- Le frontend utilise le Next.js App Router.
- Le stepper initial ne connaissait que trois états et présentait six étapes dans un ordre incompatible avec le parcours demandé.
- La page générale des formateurs affichait `Sélectionner` sans toujours disposer d'un identifiant de dossier.
- Les dates de création étaient vides et la correction d'une fin antérieure n'était pas automatique.
- Les entreprises, contacts et thèmes ne pouvaient pas être créés ou saisis sans quitter le formulaire.
- Le backend persistait déjà `trainer_id`, mais ses transitions historiques plaçaient le formateur avant le besoin.

## Nouveau parcours

1. Demande
2. Besoin
3. Formateur
4. Accord de principe
5. Programme
6. Prix
7. Acceptation finale
8. Documents

Le backend reste la source de vérité. Les anciennes transitions compatibles ont été conservées pour ne pas casser les dossiers déjà engagés, tandis que le nouveau parcours passe par le besoin avant la recherche du formateur.

## Corrections

- Stepper à huit étapes avec états terminé, actuel, disponible et verrouillé.
- Explication affichée pour chaque étape verrouillée et compteur `Étape n sur 8`.
- Composant réutilisable `WorkflowActionBar`, sticky et responsive.
- Création rapide d'une entreprise avec son nom via la vraie API.
- Chargement des contacts après sélection de l'entreprise et création rapide d'un contact.
- Thème libre avec suggestions fréquentes, enregistré comme texte du dossier.
- Dates initialisées avec la date locale du jour.
- Si le début dépasse la fin, la fin est automatiquement alignée sur le début.
- Validation frontend et backend de la période.
- Création réelle, transitions réelles et redirection vers Besoin.
- Validation du besoin puis redirection vers l'affectation du formateur.
- Affectation réelle via `POST /api/training-cases/{id}/trainer`.
- Sélection persistante après refetch/rechargement, avec feedback visuel et action de confirmation.
- Les actions d'archivage sont absentes de l'écran d'affectation.

## API utilisées

- `POST /api/training-cases`
- `POST /api/training-cases/{id}/change-status`
- `GET /api/training-cases/{id}`
- `POST /api/training-cases/{id}/need`
- `PATCH /api/training-cases/{id}/need`
- `POST /api/training-cases/{id}/need/validate`
- `GET /api/companies`
- `POST /api/companies`
- `GET /api/companies/{id}`
- `POST /api/companies/{id}/contacts`
- `GET /api/trainers`
- `POST /api/training-cases/{id}/trainer`

## Validation

- Backend : 81 tests réussis, 1 ignoré.
- Ruff : réussi.
- MyPy : réussi sur 85 fichiers.
- Frontend : 33 tests réussis.
- ESLint : réussi.
- Build Next.js : réussi.
- E2E réel : 1 scénario réussi.
- Validation navigateur : dates locales, huit étapes, verrouillages, utilisateur dynamique et persistance du formateur vérifiés.

## Limites conservées

- Aucun RAG, email, n8n ou OCR d'image n'a été ajouté.
- La disponibilité détaillée par calendrier n'existe pas dans le modèle backend : l'interface considère uniquement les formateurs actifs comme sélectionnables.
- Accord de principe et acceptation finale sont représentés dans le parcours autour des transitions métier existantes; aucune fausse donnée ni table artificielle n'a été créée.
