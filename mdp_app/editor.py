from __future__ import annotations

import os
import shutil
import subprocess


def avertir_mdp_faible(mdp: str) -> None:
    if len(mdp) < 12:
        print("Mot de passe court: utilise idéalement une phrase de passe (12+ caractères).")


def ouvrir_editeur(path: str) -> None:
    code = shutil.which("code")
    if code:
        subprocess.Popen([code, path])
        return

    if os.name == "nt":
        os.startfile(os.path.abspath(path))
        return

    opener = shutil.which("xdg-open") or shutil.which("open")
    if opener:
        subprocess.Popen([opener, path])


def confirmer_fin_edition() -> bool:
    reponse = input(
        "\nQuand tu as fini d'éditer, appuie sur Entrée pour rechiffrer (ou tape 'a' pour annuler) : "
    ).strip().lower()
    return reponse != "a"
