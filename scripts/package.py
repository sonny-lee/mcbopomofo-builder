"""Package cmake install output into fcitx5-plugins split archives (-arch & -any)."""

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from dirhash import dirhash


INPUT_METHODS = ["mcbopomofo", "mcbopomofo-plain"]


def _collect_files(roots: tuple[Path, ...]) -> list[str]:
    """Collect relative file paths across staging directories excluding plugin/."""
    files: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for dirpath, _, filenames in os.walk(root):
            cur = Path(dirpath)
            if cur == root / "plugin":
                continue
            for filename in filenames:
                rel = (cur / filename).relative_to(root).as_posix()
                files.append(rel)
    files.sort()
    return files


def _tar_bz2(src_dir: Path, archive_path: Path) -> None:
    """Create a .tar.bz2 archive without macOS extended attributes."""
    subprocess.run(
        ["tar", "cjf", str(archive_path), "--no-xattrs", "."],
        cwd=src_dir,
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Split-package mcbopomofo for macOS.")
    parser.add_argument("--stage-dir", required=True, type=Path, help="DESTDIR usr staging root")
    parser.add_argument("--out-dir", required=True, type=Path, help="Output directory for archives")
    parser.add_argument("--arch", required=True, choices=["arm64", "x86_64"], help="Target arch")
    args = parser.parse_args()

    stage_dir: Path = args.stage_dir.resolve()
    out_dir: Path = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    usr_dir = stage_dir / "usr"
    data_dir = stage_dir / "data"

    # Mirror fcitx5-plugins scripts/install.sh cleanup
    for rel in ("include", "lib/cmake", "share/metainfo"):
        target = usr_dir / rel
        if target.exists():
            shutil.rmtree(target)

    so_path = usr_dir / "lib" / "fcitx5" / "mcbopomofo.so"
    if not so_path.is_file():
        raise FileNotFoundError(f"Missing built plugin module: {so_path}")

    subprocess.run(["strip", "-x", str(so_path)], check=True)

    if data_dir.exists():
        shutil.rmtree(data_dir)
    data_dir.mkdir(parents=True)

    share_src = usr_dir / "share"
    if share_src.exists():
        shutil.move(str(share_src), str(data_dir / "share"))

    files = _collect_files((usr_dir, data_dir))
    version = dirhash(str(usr_dir), "md5", ignore=["plugin"])
    data_version = dirhash(str(data_dir), "md5")

    descriptor: dict[str, Any] = {
        "files": files,
        "data_version": data_version,
        "version": version,
        "input_methods": INPUT_METHODS,
    }

    for target_root in (data_dir, usr_dir):
        plugin_dir = target_root / "plugin"
        plugin_dir.mkdir(parents=True, exist_ok=True)
        (plugin_dir / "mcbopomofo.json").write_text(
            json.dumps(descriptor, indent=2) + "\n",
            encoding="utf-8",
        )

    _tar_bz2(usr_dir, out_dir / f"mcbopomofo-{args.arch}.tar.bz2")
    _tar_bz2(data_dir, out_dir / "mcbopomofo-any.tar.bz2")

    print(f"Packaged mcbopomofo-{args.arch}.tar.bz2 and mcbopomofo-any.tar.bz2")
    print(f"version={version} data_version={data_version}")


if __name__ == "__main__":
    main()
