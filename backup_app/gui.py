from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .core import run_backup
from mdp_app.ui_style import apply_style


class App(ttk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=12)
        self.master = master
        self.master.title("backup — Sauvegarde")
        self.pack(fill="both", expand=True)

        self.src_var = tk.StringVar()
        self.dst_var = tk.StringVar()

        self.status_var = tk.StringVar(value="Prêt.")
        self.progress_var = tk.IntVar(value=0)
        self.progress_max = tk.IntVar(value=100)

        self._q: queue.Queue[tuple[str, object]] = queue.Queue()
        self._worker: threading.Thread | None = None

        self._build()
        self.master.after(50, self._poll)

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)

        paths = ttk.Labelframe(self, text="Dossiers")
        paths.grid(row=0, column=0, sticky="ew")
        paths.columnconfigure(1, weight=1)

        ttk.Label(paths, text="Source").grid(row=0, column=0, sticky="w")
        ttk.Entry(paths, textvariable=self.src_var).grid(row=0, column=1, sticky="ew", padx=(8, 8))
        ttk.Button(paths, text="Parcourir…", command=self._pick_src).grid(row=0, column=2)

        ttk.Label(paths, text="Destination").grid(row=1, column=0, sticky="w", pady=(10, 0))
        ttk.Entry(paths, textvariable=self.dst_var).grid(row=1, column=1, sticky="ew", padx=(8, 8), pady=(10, 0))
        ttk.Button(paths, text="Parcourir…", command=self._pick_dst).grid(row=1, column=2, pady=(10, 0))

        actions = ttk.Frame(self)
        actions.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        actions.columnconfigure(0, weight=1)
        ttk.Label(actions, text="Copie miroir: les fichiers sont recopiés à l’identique.", style="Muted.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.btn_backup = ttk.Button(actions, text="Sauvegarder", command=self.backup, style="Primary.TButton")
        self.btn_backup.grid(row=0, column=1, sticky="e")

        prog = ttk.Labelframe(self, text="Progression")
        prog.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        prog.columnconfigure(0, weight=1)

        self.pbar = ttk.Progressbar(
            prog,
            orient="horizontal",
            mode="determinate",
            maximum=100,
            variable=self.progress_var,
        )
        self.pbar.grid(row=0, column=0, sticky="ew")
        ttk.Label(prog, textvariable=self.status_var).grid(row=1, column=0, sticky="w", pady=(8, 0))

    def _pick_src(self) -> None:
        p = filedialog.askdirectory(title="Choisir le dossier source")
        if p:
            self.src_var.set(p)

    def _pick_dst(self) -> None:
        p = filedialog.askdirectory(title="Choisir le dossier destination")
        if p:
            self.dst_var.set(p)

    def _set_busy(self, busy: bool) -> None:
        self.btn_backup.state(["disabled"] if busy else ["!disabled"])

    def _progress(self, done: int, total: int, msg: str) -> None:
        self._q.put(("progress", (done, total, msg)))

    def _start_worker(self, fn, *args) -> None:
        if self._worker and self._worker.is_alive():
            messagebox.showinfo("Info", "Une opération est déjà en cours.")
            return

        self._set_busy(True)
        self.progress_var.set(0)
        self.pbar.configure(maximum=100)
        self.status_var.set("Démarrage…")

        def run():
            try:
                fn(*args)
            except Exception as e:
                self._q.put(("error", str(e)))
            finally:
                self._q.put(("done", None))

        self._worker = threading.Thread(target=run, daemon=True)
        self._worker.start()

    def _poll(self) -> None:
        try:
            while True:
                kind, payload = self._q.get_nowait()
                if kind == "progress":
                    done, total, msg = payload  # type: ignore[misc]
                    if total and total > 0:
                        self.pbar.configure(maximum=total)
                        self.progress_var.set(done)
                    self.status_var.set(msg)
                elif kind == "error":
                    messagebox.showerror("Erreur", str(payload))
                elif kind == "info":
                    messagebox.showinfo("OK", str(payload))
                elif kind == "done":
                    self._set_busy(False)
        except queue.Empty:
            pass
        self.master.after(80, self._poll)

    def backup(self) -> None:
        src = self.src_var.get().strip()
        dst = self.dst_var.get().strip()
        if not src or not dst:
            messagebox.showerror("Erreur", "Source et Destination sont requis.")
            return

        def _do():
            res = run_backup(src, dst, progress=self._progress)
            if res.errors:
                self._q.put(("info", f"Sauvegarde terminée avec erreurs ({len(res.errors)}). Voir backup.log"))
            else:
                self._q.put(("info", "Sauvegarde OK."))

        self._start_worker(_do)


def main(*, theme: str = "auto") -> None:
    root = tk.Tk()

    apply_style(root, theme=theme)

    App(root)
    root.minsize(760, 420)
    root.mainloop()
