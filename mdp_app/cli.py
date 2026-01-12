from __future__ import annotations

import getpass
import os
import time

from cryptography.fernet import InvalidToken

from .config import FICHIER, FICHIER_CLAIR
from .crypto import chiffrer_bytes_v4, dechiffrer_bytes, decoder
from .editor import avertir_mdp_faible, confirmer_fin_edition, ouvrir_editeur
from .storage import ecrire_chiffre, ecrire_clair, lire_chiffre, lire_clair


def _attente_apres_echec(tentative: int) -> None:
    delai = min(2.0 * tentative, 10.0)
    time.sleep(delai)


def chiffrer_depuis_fichier(mdp: str, chemin_clair: str = FICHIER_CLAIR) -> None:
    avertir_mdp_faible(mdp)
    contenu = lire_clair(chemin_clair)
    data = chiffrer_bytes_v4(mdp, contenu, salt=os.urandom(16))
    ecrire_chiffre(data)


def creer_et_editer_puis_chiffrer() -> None:
    mdp = getpass.getpass("Créer le mot de passe : ")
    mdp2 = getpass.getpass("Confirmer le mot de passe : ")
    if mdp != mdp2:
        print("Les mots de passe ne correspondent pas")
        return

    if not os.path.exists(FICHIER_CLAIR):
        ecrire_clair(b"", FICHIER_CLAIR)

    print(f"\nOuverture de {FICHIER_CLAIR} pour édition…")
    try:
        ouvrir_editeur(FICHIER_CLAIR)
        if not confirmer_fin_edition():
            print("Annulé. Le fichier en clair est conservé :")
            print(f"   {FICHIER_CLAIR}")
            return
    except KeyboardInterrupt:
        print("\nInterrompu. Le fichier en clair est conservé :")
        print(f"   {FICHIER_CLAIR}")
        print("   Relance le script et choisis l'option 2 pour rechiffrer.")
        return

    chiffrer_depuis_fichier(mdp, FICHIER_CLAIR)
    try:
        os.remove(FICHIER_CLAIR)
    except FileNotFoundError:
        pass
    print("Chiffré. Le contenu en clair n'est plus présent.")


def dechiffrer_vers_fichier() -> None:
    tentative = 0
    while True:
        mdp = getpass.getpass("Mot de passe : ")
        tentative += 1
        try:
            raw = lire_chiffre()
            version = decoder(raw)[0]
            contenu = dechiffrer_bytes(mdp, raw)

            # Migration automatique: une fois le mot de passe validé,
            # on réécrit en v3 (anti-`strings`).
            if version != "v4":
                try:
                    ecrire_chiffre(chiffrer_bytes_v4(mdp, contenu, salt=os.urandom(16)))
                except Exception:
                    pass
            break
        except (InvalidToken, FileNotFoundError):
            print("Mot de passe incorrect ou fichier corrompu")
            _attente_apres_echec(tentative)
            if tentative >= 3:
                return

    ecrire_clair(contenu, FICHIER_CLAIR)

    print(f"\nDéchiffré vers {FICHIER_CLAIR}.")
    try:
        ouvrir_editeur(FICHIER_CLAIR)
        if not confirmer_fin_edition():
            print("Annulé. Le fichier en clair est conservé :")
            print(f"   {FICHIER_CLAIR}")
            print("   Relance le script et choisis l'option 2 pour rechiffrer.")
            return
    except KeyboardInterrupt:
        print("\nInterrompu. Le fichier en clair est conservé :")
        print(f"   {FICHIER_CLAIR}")
        print("   Relance le script et choisis l'option 2 pour rechiffrer.")
        return

    try:
        chiffrer_depuis_fichier(mdp, FICHIER_CLAIR)
        os.remove(FICHIER_CLAIR)
    except Exception as e:
        print("Erreur pendant le rechiffrement. Le fichier en clair est conservé:")
        print(f"   {FICHIER_CLAIR}")
        print(f"   Détail: {e}")
        return

    print("Rechiffré. Le fichier en clair a été supprimé.")


def rechiffrer_fichier_clair_existant() -> None:
    if not os.path.exists(FICHIER_CLAIR):
        print(f"Aucun fichier en clair à rechiffrer ({FICHIER_CLAIR} introuvable)")
        return

    mdp = getpass.getpass("Mot de passe : ")
    try:
        chiffrer_depuis_fichier(mdp, FICHIER_CLAIR)
        os.remove(FICHIER_CLAIR)
    except Exception as e:
        print("Erreur pendant le rechiffrement. Le fichier en clair est conservé:")
        print(f"   {FICHIER_CLAIR}")
        print(f"   Détail: {e}")
        return

    print("Rechiffré. Le fichier en clair a été supprimé.")


def afficher_contenu() -> None:
    tentative = 0
    while True:
        mdp = getpass.getpass("Mot de passe : ")
        tentative += 1
        try:
            raw = lire_chiffre()
            version = decoder(raw)[0]
            contenu = dechiffrer_bytes(mdp, raw)

            if version != "v4":
                try:
                    ecrire_chiffre(chiffrer_bytes_v4(mdp, contenu, salt=os.urandom(16)))
                except Exception:
                    pass
            break
        except (InvalidToken, FileNotFoundError):
            print("Mot de passe incorrect ou fichier corrompu")
            _attente_apres_echec(tentative)
            if tentative >= 3:
                return

    print("\nContenu déchiffré :")
    try:
        print(contenu.decode())
    except UnicodeDecodeError:
        print(contenu)


def main() -> None:
    if not os.path.exists(FICHIER):
        creer_et_editer_puis_chiffrer()
        return

    print("\nQue veux-tu faire ?")
    print("1) Voir le contenu (décrypté dans le terminal)")
    print("2) Éditer (si secret.txt existe: rechiffrer / sinon: déchiffrer→éditer→rechiffrer)")
    choix = input("Choix [1/2] : ").strip() or "2"

    if choix == "1":
        afficher_contenu()
    else:
        if os.path.exists(FICHIER_CLAIR):
            rechiffrer_fichier_clair_existant()
        else:
            dechiffrer_vers_fichier()
