from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

VAULT_MAGIC = "MDP_VAULT"
VAULT_VERSION = 1


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class VaultEntry:
    id: str
    title: str
    username: str
    password: str
    notes: str
    updated_at: str

    @staticmethod
    def new(*, title: str = "", username: str = "", password: str = "", notes: str = "") -> "VaultEntry":
        return VaultEntry(
            id=str(uuid.uuid4()),
            title=title,
            username=username,
            password=password,
            notes=notes,
            updated_at=_now_iso(),
        )


@dataclass
class Vault:
    entries: list[VaultEntry]


def new_empty_vault() -> Vault:
    return Vault(entries=[])


def load_vault_from_bytes(data: bytes) -> Vault:
    """Parse decrypted bytes.

    - If JSON vault format: load entries.
    - If not JSON: treat as legacy text and import as a single entry in notes.
    """

    text = data.decode("utf-8", errors="replace").strip("\ufeff")
    if not text:
        return new_empty_vault()

    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        legacy = VaultEntry.new(title="Import (ancien format)", notes=text)
        return Vault(entries=[legacy])

    if not isinstance(obj, dict):
        legacy = VaultEntry.new(title="Import (ancien format)", notes=text)
        return Vault(entries=[legacy])

    if obj.get("magic") != VAULT_MAGIC or obj.get("version") != VAULT_VERSION:
        legacy = VaultEntry.new(title="Import (ancien format)", notes=text)
        return Vault(entries=[legacy])

    entries_raw = obj.get("entries", [])
    if not isinstance(entries_raw, list):
        return new_empty_vault()

    entries: list[VaultEntry] = []
    for item in entries_raw:
        if not isinstance(item, dict):
            continue
        entries.append(
            VaultEntry(
                id=str(item.get("id") or uuid.uuid4()),
                title=str(item.get("title") or ""),
                username=str(item.get("username") or ""),
                password=str(item.get("password") or ""),
                notes=str(item.get("notes") or ""),
                updated_at=str(item.get("updated_at") or _now_iso()),
            )
        )

    return Vault(entries=entries)


def dump_vault_to_bytes(vault: Vault) -> bytes:
    obj: dict[str, Any] = {
        "magic": VAULT_MAGIC,
        "version": VAULT_VERSION,
        "updated_at": _now_iso(),
        "entries": [
            {
                "id": e.id,
                "title": e.title,
                "username": e.username,
                "password": e.password,
                "notes": e.notes,
                "updated_at": e.updated_at,
            }
            for e in vault.entries
        ],
    }
    return (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
