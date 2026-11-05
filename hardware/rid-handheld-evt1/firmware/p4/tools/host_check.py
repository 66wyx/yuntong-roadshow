"""Build and run every host-side check for the P4 receiver.

    python tools/host_check.py [--cc "zig cc"] [--preview-dir DIR]

Compiles the portable modules (decoder, geometry, graphics, fonts, UI) with
-Werror, runs the C unit tests and the ctypes fixture test, checks font
coverage, and renders UI previews. Needs a C11 compiler: cc/gcc/clang on PATH,
or `python -m pip install ziglang` and pass --cc "python -m ziglang cc".
Pillow is needed for font coverage and PNG previews.

This does not build ESP-IDF firmware or exercise hardware.
"""

from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
MAIN = PROJECT / "main"
PORTABLE = ("rid_decoder.c", "rid_geo.c", "rid_gfx.c", "rid_ui.c",
            "ui_font.c", "ui_font_data.c")
FLAGS = ("-std=gnu11", "-O2", "-Wall", "-Wextra", "-Werror", "-Wshadow")


def compiler(choice: str | None) -> list[str]:
    if choice:
        return shlex.split(choice)
    for name in ("cc", "gcc", "clang"):
        if shutil.which(name):
            return [name]
    raise SystemExit("No C compiler found; pass --cc")


def run(command: list[str], **kwargs) -> None:
    print("+", " ".join(str(part) for part in command), flush=True)
    subprocess.run([str(part) for part in command], check=True, **kwargs)


def ppm_to_png(directory: Path) -> None:
    try:
        from PIL import Image
    except ImportError:
        print("Pillow missing; previews left as PPM")
        return
    for ppm in sorted(directory.glob("*.ppm")):
        Image.open(ppm).save(ppm.with_suffix(".png"))
        ppm.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cc", help='compiler command, e.g. "python -m ziglang cc"')
    parser.add_argument("--preview-dir", type=Path,
                        help="write UI previews here (PNG when Pillow is available)")
    args = parser.parse_args()
    cc = compiler(args.cc)
    sources = [MAIN / name for name in PORTABLE]
    exe = ".exe" if sys.platform == "win32" else ""

    run([sys.executable, PROJECT / "tools" / "gen_ui_font.py", "--check"])
    with tempfile.TemporaryDirectory(prefix="rid-p4-host-") as temp:
        temp_dir = Path(temp)
        tests = temp_dir / f"rid_host_tests{exe}"
        run([*cc, *FLAGS, f"-I{MAIN}", *sources,
             PROJECT / "host" / "rid_host_tests.c", "-lm", "-o", tests])
        run([tests])

        library = temp_dir / ("rid_decoder.dll" if sys.platform == "win32"
                              else "librid_decoder.so")
        run([*cc, *FLAGS, "-shared", "-fPIC", f"-I{MAIN}",
             MAIN / "rid_decoder.c", "-o", library])
        run([sys.executable, PROJECT / "tools" / "test_rid_decoder.py", library])

        if args.preview_dir:
            preview = temp_dir / f"ui_preview{exe}"
            run([*cc, *FLAGS, f"-I{MAIN}", *sources,
                 PROJECT / "host" / "ui_preview.c", "-lm", "-o", preview])
            args.preview_dir.mkdir(parents=True, exist_ok=True)
            run([preview, args.preview_dir], stdout=subprocess.DEVNULL)
            ppm_to_png(args.preview_dir)
    print("P4 host checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
