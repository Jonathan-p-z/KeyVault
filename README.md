# mdp — Coffre de mots de passe chiffré + backup

Ce repo contient une application avec 2 outils :

- **MDP** : gestionnaire de mots de passe dans un coffre chiffré.
- **Backup** : copie “miroir” d’un dossier (GUI + CLI).

## Sécurité (résumé)

- Chiffrement/déchiffrement : `cryptography` (Fernet).
- Dérivation de clé : **Argon2id** (format **v4**) + sel aléatoire.
- Anti-`strings` : le coffre est encodé pour éviter d’exposer des marqueurs ASCII (utile contre des inspections rapides type `strings`).
- Compatibilité : lecture des anciens formats (legacy/v2/v3) + migration automatique vers v4 après déchiffrement.

## Où est stocké le coffre ?

- Windows : `%APPDATA%\mdp_app\vault.bin` (marqué “caché + système”).
- Linux : `~/.mdp_app/vault.bin`.

## Lancer le projet

### Option A — Windows (recommandé)

1) Installer Python 3.10+ : https://www.python.org/downloads/
2) Double-cliquer sur `run.bat`

Alternative PowerShell :

```powershell
.\run.ps1
.\run.ps1 -Theme clam
```

### Option B — Ligne de commande (Windows/Linux)

Créer/activer le venv :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Installer les dépendances :

```powershell
pip install -r requirements.txt
```

Lancer l’app (menu GUI : choisir MDP / Backup) :

```powershell
python -m mdp_app
```

Accès direct (optionnel) :

```powershell
python app.py --mdp
python app.py --backup
```

## Backup

### GUI

```powershell
python backup.py --gui
```

### CLI (copie)

```powershell
python backup.py --src "C:\source" --dst "D:\dest"
```

### CLI (miroir strict — DANGEREUX)

Supprime dans la destination ce qui n’existe plus dans la source :

```powershell
python backup.py --src "C:\source" --dst "D:\dest" --mirror-delete
```

## Développement (qualité)

Installer les deps dev :

```powershell
pip install -r requirements-dev.txt
```

Lint :

```powershell
ruff check .
```

Tests :

```powershell
pytest
```

CI : GitHub Actions lance `ruff` + `pytest` sur Windows et Linux.

## Build des exécutables (PyInstaller)

```powershell
pyinstaller mdp_app.spec
pyinstaller backup.spec
```

Résultat : `dist\mdp_app.exe` et `dist\backup.exe`.

## Licence

MIT — voir `LICENSE`.
