from __future__ import annotations

import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from .logging_utils import get_logger


@dataclass(frozen=True)
class BackupResult:
    copied_files: int
    errors: list[str]


def _iter_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file():
            yield p


def _ensure_dir_exists(p: Path, label: str, *, create: bool = False) -> None:
    if not p.exists():
        if create:
            p.mkdir(parents=True, exist_ok=True)
        else:
            raise FileNotFoundError(f"{label} introuvable: {p}")
    if not p.is_dir():
        raise NotADirectoryError(f"{label} n'est pas un dossier: {p}")


def _copy_with_retries(src: Path, dst: Path, *, retries: int = 3, delay_s: float = 0.25) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    last_exc: Exception | None = None
    for i in range(retries):
        try:
            shutil.copy2(src, dst)
            return
        except PermissionError as e:
            last_exc = e
            time.sleep(delay_s * (i + 1))
        except OSError as e:
            last_exc = e
            time.sleep(delay_s * (i + 1))
    assert last_exc is not None
    raise last_exc


def run_backup(
    src_dir: str | Path,
    dst_dir: str | Path,
    *,
    progress: Callable[[int, int, str], None] | None = None,
    log_path: str | Path = "backup.log",
) -> BackupResult:
    logger = get_logger(log_path)

    src = Path(src_dir)
    dst = Path(dst_dir)
    _ensure_dir_exists(src, "Dossier source")
    # UX: créer automatiquement la destination si besoin.
    _ensure_dir_exists(dst, "Dossier destination", create=True)

    files = list(_iter_files(src))
    total = len(files)
    copied = 0
    errors: list[str] = []

    logger.info("=== SAUVEGARDE START ===")
    logger.info("Source: %s", src)
    logger.info("Destination: %s", dst)
    logger.info("Fichiers detectés: %d", total)

    if progress:
        progress(0, total, "Démarrage…")

    for idx, f in enumerate(files, start=1):
        rel = f.relative_to(src)
        target = dst / rel
        try:
            _copy_with_retries(f, target, retries=3)
            copied += 1
            if progress:
                progress(idx, total, f"Copie: {rel}")
        except Exception as e:
            msg = f"Erreur copie {rel}: {e}"
            errors.append(msg)
            logger.error(msg)
            if progress:
                progress(idx, total, f"Erreur: {rel}")

    logger.info("Copiés: %d/%d", copied, total)
    if errors:
        logger.info("Erreurs: %d (voir détails ci-dessus)", len(errors))
    logger.info("=== SAUVEGARDE END ===")

    return BackupResult(copied_files=copied, errors=errors)
