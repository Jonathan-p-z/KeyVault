from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .config import FICHIER, FICHIER_CLAIR, LEGACY_APPDATA_FICHIER, LEGACY_FICHIER


def _hide_on_windows(path: Path) -> None:
    if os.name != "nt":
        return
    try:
        import ctypes

        FILE_ATTRIBUTE_HIDDEN = 0x2
        FILE_ATTRIBUTE_SYSTEM = 0x4
        ctypes.windll.kernel32.SetFileAttributesW(str(path), FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)
    except Exception:
        pass


def _harden_acl_on_windows(path: Path) -> None:
    if os.name != "nt":
        return
    try:
        # IMPORTANT: ne jamais retirer l'héritage (/inheritance:r) ici.
        # Ça peut verrouiller le dossier si l'identité n'est pas correctement résolue
        # (ex: comptes Microsoft/AzureAD, WSL interop, etc.).

        # Récupère le SID de l'utilisateur courant pour un grant robuste.
        def _current_user_sid() -> str | None:
            import ctypes
            from ctypes import wintypes

            advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

            TOKEN_QUERY = 0x0008
            TokenUser = 1

            class SID_AND_ATTRIBUTES(ctypes.Structure):
                _fields_ = [("Sid", wintypes.LPVOID), ("Attributes", wintypes.DWORD)]

            class TOKEN_USER(ctypes.Structure):
                _fields_ = [("User", SID_AND_ATTRIBUTES)]

            OpenProcessToken = advapi32.OpenProcessToken
            OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
            OpenProcessToken.restype = wintypes.BOOL

            GetTokenInformation = advapi32.GetTokenInformation
            GetTokenInformation.argtypes = [
                wintypes.HANDLE,
                wintypes.DWORD,
                wintypes.LPVOID,
                wintypes.DWORD,
                ctypes.POINTER(wintypes.DWORD),
            ]
            GetTokenInformation.restype = wintypes.BOOL

            ConvertSidToStringSidW = advapi32.ConvertSidToStringSidW
            ConvertSidToStringSidW.argtypes = [wintypes.LPVOID, ctypes.POINTER(wintypes.LPWSTR)]
            ConvertSidToStringSidW.restype = wintypes.BOOL

            LocalFree = kernel32.LocalFree
            LocalFree.argtypes = [wintypes.HLOCAL]
            LocalFree.restype = wintypes.HLOCAL

            token = wintypes.HANDLE()
            if not OpenProcessToken(kernel32.GetCurrentProcess(), TOKEN_QUERY, ctypes.byref(token)):
                return None
            try:
                needed = wintypes.DWORD(0)
                GetTokenInformation(token, TokenUser, None, 0, ctypes.byref(needed))
                buf = ctypes.create_string_buffer(needed.value)
                if not GetTokenInformation(token, TokenUser, buf, needed.value, ctypes.byref(needed)):
                    return None

                tu = ctypes.cast(buf, ctypes.POINTER(TOKEN_USER)).contents
                sid_ptr = tu.User.Sid

                sid_str = wintypes.LPWSTR()
                if not ConvertSidToStringSidW(sid_ptr, ctypes.byref(sid_str)):
                    return None
                try:
                    return sid_str.value
                finally:
                    LocalFree(sid_str)
            finally:
                kernel32.CloseHandle(token)

        sid = _current_user_sid()
        if not sid:
            return

        # icacls accepte les SIDs avec un '*' (ex: *S-1-5-21-...).
        principal = f"*{sid}"

        # Active l'héritage (si possible) et donne Full Control à l'utilisateur courant.
        subprocess.run(
            ["icacls", str(path), "/inheritance:e"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        if path.exists() and path.is_dir():
            grant = f"{principal}:(OI)(CI)F"
        else:
            grant = f"{principal}:(F)"

        subprocess.run(
            ["icacls", str(path), "/grant", grant],
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
    # Écriture atomique: écrire dans un fichier temporaire puis remplacer.
    # Sur Windows, cela évite certains "Permission denied" lors d'un overwrite direct.
    tmp = p.with_suffix(p.suffix + ".tmp")
    try:
        tmp.write_bytes(data)
        try:
            os.replace(tmp, p)
        finally:
            if tmp.exists():
                try:
                    tmp.unlink()
                except Exception:
                    pass
    except PermissionError:
        # Tentative de réparation soft des ACL puis retry.
        _harden_acl_on_windows(p.parent)
        _harden_acl_on_windows(p)
        tmp.write_bytes(data)
        os.replace(tmp, p)
    _hide_on_windows(p)
    _harden_acl_on_windows(p)


def lire_clair(path: str | Path = FICHIER_CLAIR) -> bytes:
    p = Path(path)
    return p.read_bytes()


def ecrire_clair(data: bytes, path: str | Path = FICHIER_CLAIR) -> None:
    p = Path(path)
    _ensure_parent(p)
    tmp = p.with_suffix(p.suffix + ".tmp")
    try:
        tmp.write_bytes(data)
        try:
            os.replace(tmp, p)
        finally:
            if tmp.exists():
                try:
                    tmp.unlink()
                except Exception:
                    pass
    except PermissionError:
        _harden_acl_on_windows(p.parent)
        _harden_acl_on_windows(p)
        tmp.write_bytes(data)
        os.replace(tmp, p)
    _hide_on_windows(p)
