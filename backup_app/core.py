from __future__ import annotations

import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

from .logging_utils import get_logger


@dataclass(frozen=True)
class BackupResult:
    copied_files: int
    deleted_files: int = 0
    errors: list[str] = field(default_factory=list)


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
    mirror_delete: bool = False,
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
    deleted = 0
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

    # Mode miroir strict (optionnel): supprimer de la destination ce qui n'existe plus en source.
    # Par sécurité, on ne supprime rien si la copie a rencontré des erreurs.
    if mirror_delete and not errors:
        src_rel_files = {str(p.relative_to(src)).replace("\\", "/") for p in files}

        # Ne jamais supprimer le fichier de log si l'utilisateur l'a placé dans la destination.
        log_abs: Path | None = None
        try:
            log_abs = Path(log_path).resolve()
        except Exception:
            log_abs = None

        dst_files = list(_iter_files(dst))
        total_del = len(dst_files)
        if progress:
            progress(0, total_del, "Nettoyage miroir…")

        for j, df in enumerate(dst_files, start=1):
            rel = str(df.relative_to(dst)).replace("\\", "/")
            if log_abs is not None:
                try:
                    if df.resolve() == log_abs:
                        if progress:
                            progress(j, total_del, f"Garde: {rel}")
                        continue
                except Exception:
                    pass

            if rel not in src_rel_files:
                try:
                    df.unlink()
                    deleted += 1
                    if progress:
                        progress(j, total_del, f"Supprime: {rel}")
                except Exception as e:
                    msg = f"Erreur suppression {rel}: {e}"
                    errors.append(msg)
                    logger.error(msg)
                    if progress:
                        progress(j, total_del, f"Erreur suppression: {rel}")
            else:
                if progress:
                    progress(j, total_del, f"Garde: {rel}")

        # Nettoyage des dossiers vides (bottom-up).
        try:
            for d in sorted([p for p in dst.rglob("*") if p.is_dir()], key=lambda p: len(str(p)), reverse=True):
                try:
                    d.rmdir()
                except OSError:
                    pass
        except Exception:
            pass

    logger.info("Copiés: %d/%d", copied, total)
    if mirror_delete:
        logger.info("Supprimés (miroir): %d", deleted)
    if errors:
        logger.info("Erreurs: %d (voir détails ci-dessus)", len(errors))
    logger.info("=== SAUVEGARDE END ===")

    return BackupResult(copied_files=copied, deleted_files=deleted, errors=errors)
