from __future__ import annotations

from dataclasses import dataclass

from .core import run_backup


@dataclass(frozen=True)
class Args:
    gui: bool
    src: str | None
    dst: str | None
    mirror_delete: bool = False
    debug: bool = False


def _progress(done: int, total: int, msg: str) -> None:
    if total <= 0:
        print(msg)
        return
    print(f"[{done:>5}/{total:<5}] {msg}", end="\r" if done < total else "\n")


def main(args: Args) -> int:
    if not args.src or not args.dst:
        print("Erreur: --src et --dst sont requis (ou utilise --gui)")
        return 2

    try:
        result = run_backup(args.src, args.dst, progress=_progress, mirror_delete=getattr(args, "mirror_delete", False))
    except Exception as e:
        print(f"Erreur: {e}")
        return 2

    extra = f", {result.deleted_files} supprimés" if getattr(args, "mirror_delete", False) else ""
    print(f"Sauvegarde terminée: {result.copied_files} fichiers{extra} -> {args.dst}")
    if result.errors:
        print(f"Erreurs: {len(result.errors)} (voir backup.log)")
        return 1
    return 0
