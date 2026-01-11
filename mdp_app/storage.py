from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .config import DATA_DIR, FICHIER, FICHIER_CLAIR, LEGACY_APPDATA_FICHIER, LEGACY_FICHIER


def _hide_on_windows(path: Path) -> None:
    if os.name != "nt":
        return
    try:
        import ctypes

        FILE_ATTRIBUTE_HIDDEN = 0x2
        FILE_ATTRIBUTE_SYSTEM = 0x4
        ctypes.windll.kernel32.SetFileAttributesW(str(path), FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)
    except Exception:
        # Best effort: if this fails, file is still encrypted.
        pass


def _harden_acl_on_windows(path: Path) -> None:
    if os.name != "nt":
        return
    # Best-effort: remove inheritance and grant only current user full control.
    # This does not make the file "invisible", but prevents other local accounts from opening it.
    try:
        username = os.environ.get("USERNAME")
        if not username:
            return
        subprocess.run(
            ["icacls", str(path), "/inheritance:r"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        subprocess.run(
            ["icacls", str(path), "/grant:r", f"{username}:(F)"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except Exception:
        pass


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _hide_on_windows(path.parent)
    _harden_acl_on_windows(path.parent)


def _maybe_migrate_legacy(default_path: Path) -> None:
    if default_path.exists():
        return

    # 1) ancien chemin dans AppData (%APPDATA%\mdp_app\secret.enc)
    legacy_appdata = Path(LEGACY_APPDATA_FICHIER)
    if legacy_appdata.exists() and legacy_appdata.is_file():
        try:
            _ensure_parent(default_path)
            legacy_appdata.replace(default_path)
            _hide_on_windows(default_path)
            _harden_acl_on_windows(default_path)
            return
        except Exception:
            pass

    # 2) ancien chemin dans le dossier courant (./secret.enc)
    legacy = Path(LEGACY_FICHIER)
    if legacy.exists() and legacy.is_file():
        try:
            _ensure_parent(default_path)
            legacy.replace(default_path)
            _hide_on_windows(default_path)
            _harden_acl_on_windows(default_path)
        except Exception:
            pass


def lire_chiffre(path: str | Path = FICHIER) -> bytes:
    p = Path(path)
    if str(p) == FICHIER:
        _maybe_migrate_legacy(p)
    return p.read_bytes()


def ecrire_chiffre(data: bytes, path: str | Path = FICHIER) -> None:
    p = Path(path)
    _ensure_parent(p)
    p.write_bytes(data)
    _hide_on_windows(p)
    _harden_acl_on_windows(p)


def lire_clair(path: str | Path = FICHIER_CLAIR) -> bytes:
    p = Path(path)
    return p.read_bytes()


def ecrire_clair(data: bytes, path: str | Path = FICHIER_CLAIR) -> None:
    p = Path(path)
    _ensure_parent(p)
    p.write_bytes(data)
    # Le clair ne devrait pas être utilisé en GUI, mais on le cache aussi.
    _hide_on_windows(p)
