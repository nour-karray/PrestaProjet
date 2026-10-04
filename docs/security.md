# Stabilisation et sécurité

## Corrections appliquées

- suppression des identifiants de démonstration codés en dur ;
- secrets MySQL et JWT obligatoires, avec un JWT d'au moins 32 caractères ;
- seed désactivé par défaut et soumis à une configuration explicite ;
- cookies d'authentification `HttpOnly`, `SameSite=Lax` et option `Secure` ;
- mots de passe hachés avec Argon2 ;
- validation des extensions, types MIME, tailles et empreintes des fichiers ;
- noms de stockage générés côté serveur et protection contre la traversée de chemin ;
- CV, PDF, secrets, bases locales et artefacts de tests exclus de Git ;
- erreurs API contrôlées sans exposer de trace interne ;
- base de test MySQL obligatoirement suffixée par `_test`.

Les tests couvrent l'authentification, les cookies, les jetons invalides ou
expirés, les comptes inactifs, les fichiers, la génération documentaire et les
transactions MySQL.

## Authentification Spring Boot (phase 3)

Le backend Spring réutilise la table `administrators` et les empreintes Argon2id
existantes sans migration de données. Les JWT HS256 conservent les claims
`sub`, `type`, `iat` et `exp`. Les jetons d'accès et de renouvellement sont
transportés exclusivement dans les cookies `access_token` et `refresh_token`,
avec `HttpOnly`, `Path=/`, `SameSite=Lax` par défaut et `Secure` configurable.

Le CORS autorise uniquement l'origine exacte définie par `FRONTEND_URL`, avec
les credentials activés. La protection CSRF Spring est temporairement
désactivée pour préserver le contrat du frontend actuel, qui n'envoie aucun
jeton anti-CSRF. `SameSite=Lax` réduit l'exposition aux requêtes cross-site mais
ne constitue pas une protection CSRF complète. Un protocole CSRF explicite doit
être ajouté avant la bascule définitive du frontend vers le backend Spring.

## Risques résiduels

- un seul profil administrateur : pas encore de contrôle d'accès multi-rôles ;
- aucune liste de révocation centralisée des JWT ;
- aucune limitation de débit applicative sur la connexion ;
- `SameSite=Lax` réduit le risque CSRF, mais aucun jeton CSRF dédié n'est utilisé ;
- les sauvegardes et le chiffrement des fichiers locaux relèvent de l'exploitation ;
- la rotation des secrets et la supervision doivent être organisées en production ;
- l'intégration LLM locale doit rester isolée et ne recevoir que les données prévues.

## Recommandations d'exploitation

En production, activez HTTPS et `AUTH_COOKIE_SECURE=true`, placez l'API derrière
un reverse proxy, limitez l'accès MySQL au réseau nécessaire, utilisez un
gestionnaire de secrets, sauvegardez MySQL et `storage/`, puis testez
régulièrement la restauration. Ne consignez jamais les mots de passe, JWT,
chaînes de connexion ou contenus sensibles des CV.

