from __future__ import annotations

import os
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from datetime import datetime, timezone

from cryptography.fernet import InvalidToken

from .config import FICHIER
from .crypto import chiffrer_bytes_v2, dechiffrer_bytes
from .editor import avertir_mdp_faible
from .storage import ecrire_chiffre, lire_chiffre
from .ui_style import apply_style
from .vault import Vault, VaultEntry, dump_vault_to_bytes, load_vault_from_bytes, new_empty_vault


class PasswordDialog(tk.Toplevel):  # <-- FIX: Toplevel est dans tkinter, pas ttk
    def __init__(self, parent: tk.Misc, *, title: str, prompt: str, confirm: bool) -> None:
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._confirm = confirm
        self.value: str | None = None

        body = ttk.Frame(self, padding=12)
        body.grid(sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        ttk.Label(body, text=prompt).grid(row=0, column=0, sticky="w")
        self.entry = ttk.Entry(body, show="•", width=40)
        self.entry.grid(row=1, column=0, sticky="ew", pady=(6, 10))

        self.entry2: ttk.Entry | None = None
        if confirm:
            ttk.Label(body, text="Confirmer :").grid(row=2, column=0, sticky="w")
            self.entry2 = ttk.Entry(body, show="•", width=40)
            self.entry2.grid(row=3, column=0, sticky="ew", pady=(6, 10))

        btns = ttk.Frame(body)
        btns.grid(row=4, column=0, sticky="e")
        ttk.Button(btns, text="Annuler", command=self._cancel).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(btns, text="OK", command=self._ok).grid(row=0, column=1)

        self.bind("<Return>", lambda _e: self._ok())
        self.bind("<Escape>", lambda _e: self._cancel())
        self.entry.focus_set()

        self.update_idletasks()
        # Centrage approximatif
        if isinstance(parent, tk.Tk):
            x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
            y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
            self.geometry(f"+{max(x,0)}+{max(y,0)}")

    def _cancel(self) -> None:
        self.value = None
        self.destroy()

    def _ok(self) -> None:
        v = self.entry.get()
        if self._confirm and self.entry2 is not None:
            v2 = self.entry2.get()
            if v != v2:
                messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas.", parent=self)
                return
        if v == "":
            messagebox.showerror("Erreur", "Mot de passe vide.", parent=self)
            return
        self.value = v
        self.destroy()


class EntryDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, *, title: str, entry: VaultEntry | None = None) -> None:
        super().__init__(parent)
        self.title(title)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self.value: VaultEntry | None = None
        self._show_pw = tk.BooleanVar(value=False)

        body = ttk.Frame(self, padding=12)
        body.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)

        ttk.Label(body, text="Titre (site/app)").grid(row=0, column=0, sticky="w")
        self.title_var = tk.StringVar(value=(entry.title if entry else ""))
        ttk.Entry(body, textvariable=self.title_var).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(body, text="Identifiant").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.user_var = tk.StringVar(value=(entry.username if entry else ""))
        ttk.Entry(body, textvariable=self.user_var).grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        ttk.Label(body, text="Mot de passe").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.pw_var = tk.StringVar(value=(entry.password if entry else ""))
        self.pw_entry = ttk.Entry(body, textvariable=self.pw_var, show="•")
        self.pw_entry.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        show = ttk.Checkbutton(body, text="Afficher", variable=self._show_pw, command=self._toggle_pw)
        show.grid(row=2, column=2, sticky="w", padx=(8, 0), pady=(8, 0))

        ttk.Label(body, text="Notes").grid(row=3, column=0, sticky="nw", pady=(8, 0))
        self.notes = tk.Text(body, height=8, wrap=tk.WORD)
        self.notes.grid(row=3, column=1, columnspan=2, sticky="nsew", padx=(8, 0), pady=(8, 0))
        body.rowconfigure(3, weight=1)
        if entry and entry.notes:
            self.notes.insert("1.0", entry.notes)

        btns = ttk.Frame(body)
        btns.grid(row=4, column=0, columnspan=3, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Annuler", command=self._cancel).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(btns, text="OK", command=self._ok).grid(row=0, column=1)

        self.bind("<Escape>", lambda _e: self._cancel())
        self.bind("<Return>", lambda _e: self._ok())
        self.pw_entry.bind("<Return>", lambda _e: self._ok())

        # Prefill focus
        (self.title_var.get() and self.user_var.get() and self.pw_entry or None)
        self.pw_entry.focus_set()

        self.update_idletasks()
        if isinstance(parent, tk.Tk):
            x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
            y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
            self.geometry(f"+{max(x,0)}+{max(y,0)}")

        self._original_id = entry.id if entry else None

    def _toggle_pw(self) -> None:
        self.pw_entry.configure(show="" if self._show_pw.get() else "•")

    def _cancel(self) -> None:
        self.value = None
        self.destroy()

    def _ok(self) -> None:
        title = self.title_var.get().strip()
        username = self.user_var.get().strip()
        password = self.pw_var.get()
        notes = self.notes.get("1.0", tk.END).rstrip("\n")

        if not title:
            messagebox.showerror("Erreur", "Le titre est requis.", parent=self)
            return

        entry = VaultEntry.new(title=title, username=username, password=password, notes=notes)
        if self._original_id:
            entry.id = self._original_id
        entry.updated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        self.value = entry
        self.destroy()


class CoffreGUI(ttk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=10)
        self.master = master

        self._mdp: str | None = None
        self._dirty = False
        self._theme = "auto"

        self._vault: Vault = new_empty_vault()
        self._filtered_ids: list[str] = []

        self._status = tk.StringVar(value="Coffre: verrouillé")

        self._build_menu()
        self._build_toolbar()
        self._build_list()
        self._build_statusbar()

        self._refresh_ui_state()
        self._update_title()

        if not os.path.exists(FICHIER):
            self._set_status("Aucun coffre trouvé — Menu > Fichier > Nouveau")
        else:
            self._set_status("Coffre trouvé — Menu > Fichier > Ouvrir")

        self.master.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- UI building

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.master)

        m_file = tk.Menu(menubar, tearoff=0)
        m_file.add_command(label="Nouveau", command=self.nouveau, accelerator="Ctrl+N")
        m_file.add_command(label="Ouvrir / Déchiffrer", command=self.ouvrir, accelerator="Ctrl+O")
        m_file.add_command(label="Enregistrer / Rechiffrer", command=self.enregistrer, accelerator="Ctrl+S")
        m_file.add_separator()
        m_file.add_command(label="Verrouiller", command=self.verrouiller, accelerator="Ctrl+L")
        m_file.add_separator()
        m_file.add_command(label="Quitter", command=self._on_close, accelerator="Ctrl+Q")
        menubar.add_cascade(label="Fichier", menu=m_file)

        m_view = tk.Menu(menubar, tearoff=0)
        m_view.add_command(label="Thème: auto", command=lambda: self.set_theme("auto"))
        m_view.add_command(label="Thème: clam", command=lambda: self.set_theme("clam"))
        if os.name == "nt":
            m_view.add_command(label="Thème: vista", command=lambda: self.set_theme("vista"))
            m_view.add_command(label="Thème: xpnative", command=lambda: self.set_theme("xpnative"))
        menubar.add_cascade(label="Affichage", menu=m_view)

        self.master.config(menu=menubar)

        # Raccourcis
        self.master.bind_all("<Control-n>", lambda _e: self.nouveau())
        self.master.bind_all("<Control-o>", lambda _e: self.ouvrir())
        self.master.bind_all("<Control-s>", lambda _e: self.enregistrer())
        self.master.bind_all("<Control-l>", lambda _e: self.verrouiller())
        self.master.bind_all("<Control-q>", lambda _e: self._on_close())

    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self)
        bar.grid(row=0, column=0, sticky="ew")
        self.columnconfigure(0, weight=1)

        self.btn_new = ttk.Button(bar, text="Nouveau", command=self.nouveau)
        self.btn_open = ttk.Button(bar, text="Ouvrir", command=self.ouvrir)
        self.btn_save = ttk.Button(bar, text="Enregistrer", command=self.enregistrer, style="Primary.TButton")
        self.btn_lock = ttk.Button(bar, text="Verrouiller", command=self.verrouiller)

        self.btn_add = ttk.Button(bar, text="Ajouter", command=self.ajouter)
        self.btn_edit = ttk.Button(bar, text="Modifier", command=self.modifier)
        self.btn_del = ttk.Button(bar, text="Supprimer", command=self.supprimer)
        self.btn_copy = ttk.Button(bar, text="Copier MDP", command=self.copier_mdp)

        self.btn_new.grid(row=0, column=0)
        self.btn_open.grid(row=0, column=1, padx=(8, 0))
        self.btn_save.grid(row=0, column=2, padx=(8, 0))
        self.btn_lock.grid(row=0, column=3, padx=(8, 0))
        ttk.Separator(bar, orient="vertical").grid(row=0, column=4, sticky="ns", padx=10)
        self.btn_add.grid(row=0, column=5)
        self.btn_edit.grid(row=0, column=6, padx=(8, 0))
        self.btn_del.grid(row=0, column=7, padx=(8, 0))
        self.btn_copy.grid(row=0, column=8, padx=(8, 0))

        ttk.Separator(self, orient="horizontal").grid(row=1, column=0, sticky="ew", pady=(10, 10))

    def _build_list(self) -> None:
        container = ttk.Frame(self)
        container.grid(row=2, column=0, sticky="nsew")
        self.rowconfigure(2, weight=1)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        search = ttk.Labelframe(container, text="Recherche")
        search.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        search.columnconfigure(1, weight=1)

        ttk.Label(search, text="Filtrer :").grid(row=0, column=0, sticky="w")
        self.search_var = tk.StringVar(value="")
        ent = ttk.Entry(search, textvariable=self.search_var)
        ent.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ttk.Label(search, text="(titre, identifiant, notes)", style="Muted.TLabel").grid(
            row=0, column=2, sticky="w", padx=(8, 0)
        )
        ent.bind("<KeyRelease>", lambda _e: self._apply_filter())

        self.tree = ttk.Treeview(container, columns=("title", "username"), show="headings", selectmode="browse")
        self.tree.heading("title", text="Titre")
        self.tree.heading("username", text="Identifiant")
        self.tree.column("title", width=260, anchor="w")
        self.tree.column("username", width=220, anchor="w")
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.tree.bind("<Double-1>", lambda _e: self.modifier())

        # Alternating row colors (best effort)
        try:
            self.tree.tag_configure("odd", background="#f6f6f6")
        except tk.TclError:
            pass

        vsb = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=1, column=1, sticky="ns")

    def _build_statusbar(self) -> None:
        ttk.Separator(self, orient="horizontal").grid(row=3, column=0, sticky="ew", pady=(10, 6))
        status = ttk.Frame(self)
        status.grid(row=4, column=0, sticky="ew")
        status.columnconfigure(0, weight=1)

        ttk.Label(status, textvariable=self._status).grid(row=0, column=0, sticky="w")
        self.lbl_lock = ttk.Label(status, text="Verrouillé", foreground="#666")
        self.lbl_lock.grid(row=0, column=1, sticky="e")

    # ---------- State / helpers

    def _set_status(self, msg: str) -> None:
        self._status.set(msg)

    def _update_title(self) -> None:
        star = " *" if self._dirty else ""
        lock = " (verrouillé)" if self._mdp is None else ""
        self.master.title(f"mdp — Coffre-fort{lock}{star}")

    def _refresh_ui_state(self) -> None:
        locked = self._mdp is None
        self.lbl_lock.configure(text="Verrouillé" if locked else "Déverrouillé")
        self.btn_save.state(["disabled"] if locked else ["!disabled"])
        for b in (self.btn_add, self.btn_edit, self.btn_del, self.btn_copy):
            b.state(["disabled"] if locked else ["!disabled"])

    def _ask_password(self, *, title: str, prompt: str, confirm: bool) -> str | None:
        dlg = PasswordDialog(self.master, title=title, prompt=prompt, confirm=confirm)
        self.master.wait_window(dlg)
        return dlg.value

    def _on_modified(self, _evt=None) -> None:
        # kept for compatibility; list UI sets dirty via _mark_dirty
        self._dirty = True
        self._update_title()

    def _mark_dirty(self) -> None:
        self._dirty = True
        self._update_title()

    def _entries_by_id(self) -> dict[str, VaultEntry]:
        return {e.id: e for e in self._vault.entries}

    def _selected_entry_id(self) -> str | None:
        sel = self.tree.selection()
        if not sel:
            return None
        return str(sel[0])

    def _refresh_tree(self) -> None:
        self.tree.delete(*self.tree.get_children())
        by_id = self._entries_by_id()
        ids = self._filtered_ids or [e.id for e in self._vault.entries]
        for i, entry_id in enumerate(ids):
            e = by_id.get(entry_id)
            if not e:
                continue
            tags = ("odd",) if (i % 2 == 1) else ()
            self.tree.insert("", "end", iid=e.id, values=(e.title, e.username), tags=tags)

    def _apply_filter(self) -> None:
        q = self.search_var.get().strip().lower()
        if not q:
            self._filtered_ids = []
            self._refresh_tree()
            return
        matched: list[str] = []
        for e in self._vault.entries:
            hay = f"{e.title} {e.username} {e.notes}".lower()
            if q in hay:
                matched.append(e.id)
        self._filtered_ids = matched
        self._refresh_tree()

    # ---------- Commands

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        style = ttk.Style(self.master)
        if theme == "auto":
            # Choix simple: utiliser le thème courant si dispo; sinon clam
            try:
                style.theme_use(style.theme_use())
            except tk.TclError:
                style.theme_use("clam")
        else:
            try:
                style.theme_use(theme)
            except tk.TclError:
                messagebox.showerror("Erreur", f"Thème ttk inconnu: {theme}")
                return

    def verrouiller(self) -> None:
        self._mdp = None
        self._refresh_ui_state()
        self._set_status("Verrouillé (mot de passe oublié).")
        self._update_title()

    def nouveau(self) -> None:
        if self._dirty and not messagebox.askyesno("Attention", "Modifications non enregistrées. Continuer ?"):
            return

        mdp = self._ask_password(title="Nouveau coffre", prompt="Créer le mot de passe :", confirm=True)
        if mdp is None:
            return
        avertir_mdp_faible(mdp)

        self._mdp = mdp
        self._vault = new_empty_vault()
        self.search_var.set("")
        self._filtered_ids = []
        self._refresh_tree()
        self._dirty = True
        self._refresh_ui_state()
        self._set_status("Nouveau coffre: ajoute des entrées puis Enregistrer.")
        self._update_title()

    def ouvrir(self) -> None:
        if not os.path.exists(FICHIER):
            messagebox.showinfo("Info", "Aucun coffre n'existe. Utilise Nouveau.")
            return
        if self._dirty and not messagebox.askyesno("Attention", "Modifications non enregistrées. Continuer ?"):
            return

        tentative = 0
        while tentative < 3:
            mdp = self._mdp or self._ask_password(title="Déverrouiller", prompt="Mot de passe :", confirm=False)
            if mdp is None:
                return
            tentative += 1
            try:
                contenu = dechiffrer_bytes(mdp, lire_chiffre())
                self._mdp = mdp

                self._vault = load_vault_from_bytes(contenu)
                self.search_var.set("")
                self._filtered_ids = []
                self._refresh_tree()
                self._dirty = False
                self._refresh_ui_state()
                self._set_status("Déverrouillé. Ajoute/modifie puis Enregistrer pour rechiffrer.")
                self._update_title()
                return
            except (InvalidToken, FileNotFoundError):
                self._mdp = None
                self._refresh_ui_state()
                messagebox.showerror("Erreur", "Mot de passe incorrect ou fichier corrompu.")

        self._set_status("Trop de tentatives. Abandon.")

    def enregistrer(self) -> None:
        mdp = self._mdp or self._ask_password(title="Déverrouiller", prompt="Mot de passe :", confirm=False)
        if mdp is None:
            return
        avertir_mdp_faible(mdp)

        contenu = dump_vault_to_bytes(self._vault)

        try:
            data = chiffrer_bytes_v2(mdp, contenu, salt=os.urandom(16))
            ecrire_chiffre(data)
            self._mdp = mdp
            self._dirty = False
            self._refresh_ui_state()
            self._set_status("Enregistré et chiffré (coffre caché).")
            self._update_title()
            messagebox.showinfo("OK", "Rechiffré et sauvegardé.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de rechiffrer/sauvegarder.\nDétail: {e}")

    def _on_close(self) -> None:
        if self._dirty and not messagebox.askyesno("Quitter", "Modifications non enregistrées. Quitter quand même ?"):
            return
        self.verrouiller()
        self.master.destroy()

    def ajouter(self) -> None:
        if self._mdp is None:
            return
        dlg = EntryDialog(self.master, title="Ajouter une entrée", entry=None)
        self.master.wait_window(dlg)
        if dlg.value is None:
            return
        self._vault.entries.append(dlg.value)
        self._apply_filter()
        self._mark_dirty()

    def modifier(self) -> None:
        if self._mdp is None:
            return
        entry_id = self._selected_entry_id()
        if not entry_id:
            return
        by_id = self._entries_by_id()
        current = by_id.get(entry_id)
        if not current:
            return
        dlg = EntryDialog(self.master, title="Modifier une entrée", entry=current)
        self.master.wait_window(dlg)
        if dlg.value is None:
            return
        for i, e in enumerate(self._vault.entries):
            if e.id == entry_id:
                self._vault.entries[i] = dlg.value
                break
        self._apply_filter()
        self._mark_dirty()

    def supprimer(self) -> None:
        if self._mdp is None:
            return
        entry_id = self._selected_entry_id()
        if not entry_id:
            return
        if not messagebox.askyesno("Confirmer", "Supprimer cette entrée ?"):
            return
        self._vault.entries = [e for e in self._vault.entries if e.id != entry_id]
        self._apply_filter()
        self._mark_dirty()

    def copier_mdp(self) -> None:
        if self._mdp is None:
            return
        entry_id = self._selected_entry_id()
        if not entry_id:
            return
        by_id = self._entries_by_id()
        e = by_id.get(entry_id)
        if not e:
            return
        self.master.clipboard_clear()
        self.master.clipboard_append(e.password)
        self.master.update()  # ensure clipboard is set
        self._set_status("Mot de passe copié dans le presse-papiers.")


def main(*, theme: str = "auto") -> None:
    root = tk.Tk()

    apply_style(root, theme=theme)

    app = CoffreGUI(root)
    app.pack(fill="both", expand=True)
    app.set_theme(theme)

    root.minsize(700, 450)
    root.mainloop()
