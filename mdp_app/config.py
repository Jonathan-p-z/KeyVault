import os
import struct
from pathlib import Path


def _default_data_dir() -> Path:
	# Stockage "user data" (hors dossier projet) pour éviter que le coffre
	# apparaisse dans le répertoire courant.
	if os.name == "nt":
		base = os.environ.get("APPDATA")
		if base:
			return Path(base) / "mdp_app"
		return Path.home() / "AppData" / "Roaming" / "mdp_app"
	return Path.home() / ".mdp_app"


DATA_DIR = _default_data_dir()

# Nom de fichier volontairement non parlant (et caché côté Windows).
VAULT_FILENAME = "vault.bin"

# Chemins par défaut (absolus) des fichiers utilisés par l'app.
FICHIER = str(DATA_DIR / VAULT_FILENAME)
FICHIER_CLAIR = str(DATA_DIR / "secret.txt")

# Anciens emplacements (historique) pour migration.
LEGACY_FICHIER = "secret.enc"  # dossier courant
LEGACY_APPDATA_FICHIER = str(DATA_DIR / "secret.enc")

MAGIC_V2 = b"MDP2"
HEADER_V2 = struct.Struct(">4s16sIII")

SCRYPT_N = 2**18  # 262144
SCRYPT_R = 8
SCRYPT_P = 1

LEGACY_SALT = b"\x9a\x01\xf3\x8c\x90\x12\xfa\xab\x8d\x01\x02\x03\x04\x05\x06\x07"
LEGACY_PBKDF2_ITERATIONS = 390000
