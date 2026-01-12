import argparse


def _parse_args():
    p = argparse.ArgumentParser(
        description="mdp - coffre-fort chiffré",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Exemples:\n"
               "  python script.py                     # mode terminal\n"
               "  python script.py --gui               # interface graphique\n"
               "  python script.py --gui --theme clam  # GUI avec thème ttk\n"
               "  python script.py --gui --theme vista # (Windows) si disponible\n"
               "\n"
               "Outil de sauvegarde (séparé):\n"
               "  python backup.py --gui\n"
               "\n"
               "Créer l'exécutable (PowerShell, commandes exactes):\n"
               "  cd C:\\Users\\jpere\\Documents\\mdp\n"
               "  .\\.venv\\Scripts\\Activate.ps1\n"
               "  python -m pip install -r requirements-dev.txt\n"
               "  pyinstaller mdp_app.spec\n"
               "  pyinstaller backup.spec\n"
               "  # Résultat: .\\dist\\mdp_app.exe et .\\dist\\backup.exe\n"
               "\n"
               "Exécutable (après PyInstaller):\n"
               "  .\\dist\\backup.exe --gui\n"
               "  .\\dist\\backup.exe -h\n",
    )
    p.add_argument("--gui", action="store_true", help="lancer l'interface graphique")
    p.add_argument(
        "--theme",
        default="auto",
        help="thème GUI ttk (auto|clam|vista|xpnative|alt|default...)",
    )
    p.add_argument("--debug", action="store_true", help="afficher les erreurs détaillées (traceback)")
    return p.parse_args()

if __name__ == "__main__":
    args = _parse_args()

    if args.gui:
        try:
            from mdp_app.gui import main as main_gui  # lazy import
            main_gui(theme=args.theme)
        except Exception as e:
            if args.debug:
                raise
            raise SystemExit(
                "Impossible de démarrer la GUI.\n"
                f"Détail: {e}\n"
                "Astuce: relance avec `python script.py --gui --debug` pour la traceback complète."
            ) from e
    else:
        from mdp_app.cli import main as main_cli  # lazy import
        main_cli()
