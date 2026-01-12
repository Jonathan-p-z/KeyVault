from __future__ import annotations

import sys
from pathlib import Path


def _add_project_root_to_syspath() -> None:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def main() -> int:
    _add_project_root_to_syspath()

    from mdp_app.config import DATA_DIR, FICHIER
    from mdp_app.storage import _harden_acl_on_windows  # type: ignore

    data_dir = Path(DATA_DIR)
    vault = Path(FICHIER)

    print(f"DATA_DIR: {data_dir}")
    print(f"VAULT:    {vault}")

    _harden_acl_on_windows(data_dir)
    if vault.exists():
        _harden_acl_on_windows(vault)

    print("OK (best effort): ACL repaired/enhanced for current user.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
