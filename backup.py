import argparse
import sys
import traceback
from datetime import datetime
from pathlib import Path

def _parse_args():
    p = argparse.ArgumentParser(
        description="backup - sauvegarde simple (copie miroir)",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Exemples:\n"
               "  python backup.py --src C:\\data --dst D:\\backup\n"
               "  python backup.py --gui\n"
               "\n"
               "Astuce (exe):\n"
               "  Double-clic sur backup.exe -> lance la GUI\n",
    )
    p.add_argument("--gui", action="store_true", help="lancer l'interface graphique")
    p.add_argument("--src", help="dossier source à sauvegarder")
    p.add_argument("--dst", help="dossier destination (copie miroir)")
    p.add_argument("--debug", action="store_true", help="afficher les erreurs détaillées (traceback)")
    return p.parse_args()

def _write_crash_log(exc: BaseException) -> Path:
    p = Path("backup_crash.log")
    content = (
        f"{datetime.now():%Y-%m-%d %H:%M:%S} | CRASH\n"
        + "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    )
    p.write_text(content, encoding="utf-8")
    return p

if __name__ == "__main__":
    args = _parse_args()
    try:
        # UX: si lancé sans args (souvent double-clic sur l'exe), ouvrir la GUI.
        no_user_args = len(sys.argv) <= 1
        if args.gui or no_user_args or (not args.src) or (not args.dst):
            from backup_app.gui import main as main_gui
            main_gui()
        else:
            from backup_app.cli import main as main_cli
            raise SystemExit(main_cli(args))
    except SystemExit:
        raise
    except Exception as e:
        crash_path = _write_crash_log(e)

        if getattr(args, "debug", False):
            raise

        # Si GUI: popup (sinon: message console)
        if getattr(args, "gui", False):
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror(
                    "backup - erreur",
                    "Le programme a rencontré une erreur.\n"
                    f"Un log a été écrit ici: {crash_path.resolve()}",
                )
                root.destroy()
            except Exception:
                pass

        raise SystemExit(
            "Erreur: le programme a planté.\n"
            f"Un log a été écrit ici: {crash_path.resolve()}\n"
            "Relance avec `--debug` pour afficher la traceback."
        )
