from __future__ import annotations

import getpass
import os
import sys
from datetime import datetime
from pathlib import Path

from cryptography.fernet import InvalidToken

# Permet d'exécuter ce script depuis n'importe quel répertoire (y compris WSL)
# sans dépendre du PYTHONPATH.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mdp_app.config import FICHIER
from mdp_app.crypto import chiffrer_bytes_v4, dechiffrer_bytes, decoder
from mdp_app.storage import ecrire_chiffre


def main() -> int:
    vault_path = Path(FICHIER)
    if not vault_path.exists():
        print(f"Aucun coffre trouvé: {vault_path}")
        return 1

    raw = vault_path.read_bytes()
    version = decoder(raw)[0]
    print(f"Coffre: {vault_path}")
    print(f"Version actuelle: {version}")

    if version == "v3":
        print("Rien à faire (déjà en v3).")
        return 0

    mdp = getpass.getpass("Mot de passe (pour migrer en v4): ")

    try:
        plaintext = dechiffrer_bytes(mdp, raw)
    except InvalidToken:
        print("Mot de passe incorrect ou coffre corrompu")
        return 2

    # Backup simple à côté du coffre
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = vault_path.with_suffix(vault_path.suffix + f".{version}.{ts}.bak")
    try:
        backup_path.write_bytes(raw)
        print(f"Backup créé: {backup_path}")
    except Exception as e:
        print(f"Impossible de créer le backup ({e}). Abandon.")
        return 3

    try:
        ecrire_chiffre(chiffrer_bytes_v4(mdp, plaintext, salt=os.urandom(16)))
    except Exception as e:
        print(f"Migration échouée: {e}")
        return 4

    # Vérification rapide
    new_raw = vault_path.read_bytes()
    new_version = decoder(new_raw)[0]
    print(f"Nouvelle version: {new_version}")
    if new_version != "v3":
        print("Attention: la migration n'a pas produit du v3.")
        return 5

    print("OK: coffre migré en v4 (Argon2id + anti-strings).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
