# Refonte de l’interface d’administration

## Diagnostic initial

Le frontend contenait douze routes fonctionnelles connectées au backend, mais
sans design system commun. Les écrans utilisaient des styles hétérogènes, une
navigation desktop fixe, des pictogrammes textuels et un nom administrateur
statique. Le backend disposait déjà des API d’authentification, entreprises,
contacts, dossiers, formateurs, CV, besoins, programmes, prix et documents.

## Réalisation

- nouvelle charte bleu nuit, violet et bleu ;
- page de connexion responsive avec véritable authentification ;
- sidebar et header communs, repliables à 1024 px ;
- nom et initiales obtenus depuis `/api/auth/me` ;
- dashboard orienté actions et alimenté par `/api/dashboard` ;
- listes entreprises et dossiers modernisées sans perte de filtres ;
- pages de création et de détail harmonisées ;
- liste et fiches formateurs, import et validation CV harmonisés ;
- stepper partagé pour le workflow réel du dossier ;
- états loading, empty et error accessibles et réutilisables ;
- protection visuelle contre la modification d’un dossier clôturé ;
- tableaux scrollables et actions utilisables sur tablette.

## Routes frontend

- `/connexion`
- `/tableau-de-bord`
- `/entreprises`, `/entreprises/nouvelle`, `/entreprises/[id]`
- `/dossiers`, `/dossiers/nouveau`, `/dossiers/[id]`
- `/formateurs`, `/formateurs/import-cv`, `/formateurs/[id]`

## API utilisées

L’interface utilise uniquement les routes FastAPI existantes : `/api/auth`,
`/api/dashboard`, `/api/companies`, `/api/contacts`, `/api/training-cases`,
`/api/trainers`, `/api/trainer-cvs`, ainsi que les sous-ressources `need`,
`program`, `pricing` et `documents`.

## Fonctions volontairement non simulées

Le backend ne fournit pas encore de recherche globale, notifications,
paramètres enregistrables, récupération de mot de passe, OCR JPG/PNG,
disponibilité formateur, accord de principe distinct ou acceptation finale
distincte. Aucun écran ni succès fictif n’a été ajouté pour ces fonctions.

Les cinq documents réellement gérés par le backend sont conservés : programme,
devis, convention, feuille de présence et attestation.

## Validation visuelle

Le rendu a été contrôlé dans le navigateur sur la connexion, le dashboard et un
dossier réel, en desktop et à 1024 px. Aucun débordement horizontal ni erreur
console n’a été détecté.

Captures :

- `docs/captures/connexion-refonte.png`
- `docs/captures/tableau-de-bord-refonte.png`
- `docs/captures/dossier-refonte.png`

