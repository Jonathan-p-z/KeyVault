from __future__ import annotations

import argparse
import sys
import traceback
import tkinter as tk
from tkinter import messagebox, ttk

from mdp_app.ui_style import apply_style


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="mdp + backup — lanceur (GUI/CLI)",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Exemples:\n"
            "  app.exe                      # ouvre le menu (MDP / Backup)\n"
            "  app.exe --mdp                # ouvre directement le gestionnaire MDP\n"
            "  app.exe --backup             # ouvre directement la GUI backup\n"
            "  app.exe --backup --src C:\\data --dst D:\\backup --backup-cli\n"
        ),
    )

    g = p.add_mutually_exclusive_group()
    g.add_argument("--mdp", action="store_true", help="ouvrir le gestionnaire de mots de passe")
    g.add_argument("--backup", action="store_true", help="ouvrir l'outil de sauvegarde")

    p.add_argument("--theme", default="auto", help="thème ttk (auto|clam|vista|xpnative|...)")

    # Options backup (mode CLI)
    p.add_argument("--src", help="dossier source à sauvegarder (backup)")
    p.add_argument("--dst", help="dossier destination (backup)")
    p.add_argument(
        "--backup-cli",
        action="store_true",
        help="exécuter la sauvegarde en mode CLI (utile si lancé depuis un terminal)",
    )

    p.add_argument("--debug", action="store_true", help="afficher les erreurs détaillées (traceback)")
    return p.parse_args()


class Launcher(ttk.Frame):
    def __init__(self, master: tk.Tk, *, args: argparse.Namespace) -> None:
        super().__init__(master, padding=16)
        self.master = master
        self._args = args

        self.master.title("mdp — Menu")
        self.pack(fill="both", expand=True)

        self._theme_var = tk.StringVar(value=args.theme)

        self._build()

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)

        if sys.platform.startswith("win"):
            title = ttk.Label(self, text="Choisir un outil", font=("Segoe UI", 14, "bold"))
        else:
            title = ttk.Label(self, text="Choisir un outil")
        title.grid(row=0, column=0, sticky="w")

        desc = ttk.Label(
            self,
            text="Deux outils dans une seule application.",
            style="Muted.TLabel",
        )
        desc.grid(row=1, column=0, sticky="w", pady=(6, 14))

        tools = ttk.Labelframe(self, text="Outils")
        tools.grid(row=2, column=0, sticky="ew")
        tools.columnconfigure(0, weight=1)
        tools.columnconfigure(1, weight=1)

        btn_mdp = ttk.Button(tools, text="Gestionnaire MDP", command=self._open_mdp, style="Primary.TButton")
        btn_backup = ttk.Button(tools, text="Backup", command=self._open_backup, style="Primary.TButton")
        btn_mdp.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        btn_backup.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        tips = ttk.Label(
            tools,
            text="Astuce: Entrée = MDP (par défaut).",
            style="Muted.TLabel",
        )
        tips.grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))

        opts = ttk.Labelframe(self, text="Apparence")
        opts.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        ttk.Label(opts, text="Thème:").grid(row=0, column=0, sticky="w")
        theme_entry = ttk.Entry(opts, textvariable=self._theme_var, width=16)
        theme_entry.grid(row=0, column=1, sticky="w", padx=(8, 0))
        ttk.Label(opts, text="(auto / clam / vista / xpnative …)", style="Muted.TLabel").grid(
            row=0, column=2, sticky="w", padx=(8, 0)
        )

        self.master.bind("<Return>", lambda _e: self._open_mdp())

    def _open_mdp(self) -> None:
        theme = self._theme_var.get().strip() or "auto"
        self.master.destroy()
        from mdp_app.gui import main as mdp_main

        mdp_main(theme=theme)

    def _open_backup(self) -> None:
        theme = self._theme_var.get().strip() or "auto"
        self.master.destroy()
        from backup_app.gui import main as backup_main

        backup_main(theme=theme)


def _run_launcher(args: argparse.Namespace) -> None:
    root = tk.Tk()

    apply_style(root, theme=args.theme)

    Launcher(root, args=args)
    root.minsize(560, 300)
    root.mainloop()


def main() -> None:
    args = _parse_args()

    try:
        # Lancement direct (sans menu)
        if args.mdp:
            from mdp_app.gui import main as mdp_main

            mdp_main(theme=args.theme)
            return

        if args.backup:
            if args.backup_cli or (args.src and args.dst):
                from backup_app.cli import Args as BackupArgs
                from backup_app.cli import main as backup_cli

                raise SystemExit(
                    backup_cli(BackupArgs(gui=False, src=args.src, dst=args.dst, debug=args.debug))
                )

            from backup_app.gui import main as backup_gui

            backup_gui(theme=args.theme)
            return

        # Par défaut : menu
        _run_launcher(args)

    except SystemExit:
        raise
    except Exception as e:
        if args.debug:
            raise

        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Erreur",
                "Le programme a rencontré une erreur.\n\n"
                f"Détail: {e}\n\n"
                "Relance avec --debug pour la traceback complète.",
            )
            root.destroy()
        except Exception:
            pass

        raise SystemExit(
            "Erreur: le programme a planté.\n"
            f"Détail: {e}\n"
            "Relance avec --debug pour afficher la traceback."
        )


if __name__ == "__main__":
    main()
