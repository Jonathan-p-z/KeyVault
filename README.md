# mdp — Gestionnaire de mots de passe chiffré (vault.bin) + backup (copie miroir)

Ce dépôt contient 2 programmes :

1) **mdp** : gestionnaire de mots de passe (coffre chiffré) stocké dans `vault.bin`.
2) **backup** : outil de sauvegarde (copie miroir) avec CLI + GUI.

---

## 1) mdp (gestionnaire de mots de passe)

### Fonctionnalités
- Chiffrement/déchiffrement via **Fernet** (AES + HMAC) de `cryptography`
- Dérivation de clé via **Scrypt** (format "v2" avec en-tête + sel + paramètres)
- Compatibilité "legacy" (PBKDF2 + sel fixe) pour relire d’anciens fichiers si besoin
- Coffre au format **JSON** (chiffré) : entrées *Titre / Identifiant / Mot de passe / Notes*
- **GUI** : liste + recherche, ajouter/modifier/supprimer, copier le mot de passe dans le presse-papiers
- **CLI** : mode “legacy” (éditeur de texte) si tu l’utilises encore

### Pré-requis
- Python 3.10+ recommandé (testé aussi sous Windows 11)
- Dépendances :
  - `cryptography`
  # mdp — Gestionnaire de mots de passe chiffré + outil de sauvegarde

  Ce repo contient **une application** avec 2 outils accessibles via une interface graphique :

  - **MDP** : gestionnaire de mots de passe chiffré (coffre).
  - **Backup** : sauvegarde d’un dossier (copie miroir).

  ---

  ## Ce que fait le programme (détails)

  ### 1) Gestionnaire de mots de passe (MDP)

  - Tu crées un **coffre chiffré** protégé par un **mot de passe maître**.
  - Le coffre contient des entrées : **Titre / Identifiant / Mot de passe / Notes**.
  - Dans la GUI, tu peux :
    - rechercher,
    - ajouter / modifier / supprimer,
    - copier le mot de passe dans le presse-papiers.

  **Chiffrement / sécurité (résumé)**
  - Chiffrement/déchiffrement via `cryptography` (Fernet).
  - Dérivation de clé avec **Scrypt** (format v2 avec en-tête + sel + paramètres).
  - Compatibilité “legacy” : lecture d’anciens fichiers si besoin.

  **Où sont stockées les données ?**
  - Le coffre est un fichier chiffré stocké hors du dossier du projet.
    - Windows : `%APPDATA%\mdp_app\vault.bin` (marqué “caché + système”)
    - Linux : `~/.mdp_app/vault.bin`

  Important : “caché” = moins visible, mais pas “inexistant”. Sans le mot de passe maître, le fichier est **inutilisable** (chiffré).

  ### 2) Backup (sauvegarde)

  - Copie un dossier **source** vers un dossier **destination** en recréant l’arborescence.
  - C’est une **copie miroir** : si un fichier existe déjà, il peut être écrasé.
  - Affiche une progression en GUI et écrit un log dans `backup.log`.

  ---

  ## Comment lancer le projet (le plus simple)

  ### Option A — Windows (recommandé, “n’importe qui”)

  1) Installer **Python 3.10+** (une seule fois) : https://www.python.org/downloads/
  2) Télécharger le repo (ZIP) et l’extraire.
  3) Double-cliquer sur `run.bat`

  Ce que fait `run.bat` :
  - crée `.venv` si besoin,
  - installe les dépendances,
  - lance `python -m mdp_app`.

  Alternative PowerShell :
  ```powershell
  .\run.ps1
  ```

  ### Option B — Ligne de commande (Windows/Linux)

  Depuis la racine du projet :
  ```powershell
  python -m venv .venv
  ```

  Activer le venv :
  - Windows (PowerShell) :
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
  - Linux/macOS :
  ```bash
  source .venv/bin/activate
  ```

  Installer les dépendances :
  ```powershell
  pip install -r requirements.txt
  ```

  Lancer l’app (menu GUI : choisir MDP ou Backup) :
  ```powershell
  python -m mdp_app
  ```

  Accès direct (optionnel) :
  ```powershell
  python -m mdp_app --mdp
  python -m mdp_app --backup
  ```

  ---

  ## Commandes utiles

  ### Thème (look GUI)
  ```powershell
  python -m mdp_app --theme vista
  python -m mdp_app --theme clam
  ```

  ### Backup (CLI)
  ```powershell
  python backup.py --src "C:\chemin\source" --dst "D:\chemin\backup"
  ```

  ---

  ## Publication GitHub (public)

  - Ne commit jamais : `vault.bin`, `secret.enc`, `secret.txt`, logs, `dist/`, `build/`.
  - Tout ça est déjà prévu dans `.gitignore`.

  ---

  ## Licence

  MIT — voir le fichier `LICENSE`.

