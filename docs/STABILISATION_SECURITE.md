# Stabilisation et sécurité

## Corrections appliquées

- suppression des identifiants de démonstration codés en dur ;
- secrets PostgreSQL et JWT obligatoires, avec un JWT d'au moins 32 caractères ;
- seed désactivé par défaut et soumis à une configuration explicite ;
- cookies d'authentification `HttpOnly`, `SameSite=Lax` et option `Secure` ;
- mots de passe hachés avec Argon2 ;
- validation des extensions, types MIME, tailles et empreintes des fichiers ;
- noms de stockage générés côté serveur et protection contre la traversée de chemin ;
- CV, PDF, secrets, bases locales et artefacts de tests exclus de Git ;
- erreurs API contrôlées sans exposer de trace interne ;
- base de test PostgreSQL obligatoirement suffixée par `_test`.

Les tests couvrent l'authentification, les cookies, les jetons invalides ou
expirés, les comptes inactifs, les fichiers, la génération documentaire et les
transactions PostgreSQL.

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
un reverse proxy, limitez l'accès PostgreSQL au réseau nécessaire, utilisez un
gestionnaire de secrets, sauvegardez PostgreSQL et `storage/`, puis testez
régulièrement la restauration. Ne consignez jamais les mots de passe, JWT,
chaînes de connexion ou contenus sensibles des CV.

