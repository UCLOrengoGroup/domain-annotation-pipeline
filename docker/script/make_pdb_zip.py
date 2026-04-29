import argparse
import importlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from contextlib import ExitStack
from pathlib import Path

try:
    gemmi = importlib.import_module("gemmi")
except ImportError:
    gemmi = None


_INVALID_ARCNAME = re.compile(r"[^A-Za-z0-9._-]+")
_MOLSTAR_PREPROCESS_CANDIDATES = [
    os.environ.get("MOLSTAR_PREPROCESS_JS"),
    "/opt/molstar/node_modules/molstar/lib/commonjs/servers/model/preprocess.js",
]


def _safe_arcname(stem: str, suffix: str) -> str:
    stem = stem.strip()
    stem = _INVALID_ARCNAME.sub("_", stem)
    stem = stem.strip("._-")
    if not stem:
        stem = "structure"
    return f"{stem}{suffix}"


def _load_list_file(list_file: Path | None) -> list[str] | None:
    if list_file is None:
        return None
    items: list[str] = []
    for raw in list_file.read_text().splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        items.append(s)
    return items


def _find_molstar_preprocess() -> str:
    for candidate in _MOLSTAR_PREPROCESS_CANDIDATES:
        if candidate and Path(candidate).is_file():
            return candidate
    raise RuntimeError(
        "Mol* preprocess CLI not found; expected MOLSTAR_PREPROCESS_JS or /opt/molstar/node_modules/molstar/lib/commonjs/servers/model/preprocess.js"
    )


def _run_molstar_bcif_to_cif(bcif_path: Path, cif_path: Path) -> None:
    preprocess_js = _find_molstar_preprocess()
    result = subprocess.run(
        ["node", preprocess_js, "-i", str(bcif_path), "-oc", str(cif_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"molstar_bcif_to_cif_failed: {detail}")
    if not cif_path.exists() or cif_path.stat().st_size == 0:
        raise RuntimeError("molstar_bcif_to_cif_missing_or_empty")


def _count_atoms(structure) -> int:
    return sum(model.count_atom_sites() for model in structure)


def _select_members(all_members: list[str], requested: list[str] | None) -> list[str]:
    # all_members are zip member names ending with .bcif
    if requested is None:
        return sorted(all_members)

    by_full = {m: m for m in all_members}
    by_base: dict[str, list[str]] = {}
    for m in all_members:
        base = Path(m).name
        by_base.setdefault(base, []).append(m)

    selected: list[str] = []
    seen: set[str] = set()

    for token in requested:
        candidates: list[str] = []
        if token.endswith(".bcif"):
            candidates.append(token)
        else:
            candidates.append(f"{token}.bcif")
            candidates.append(token)

        picked: str | None = None

        for c in candidates:
            if c in by_full:
                picked = by_full[c]
                break

        if picked is None:
            # Try basename match
            for c in candidates:
                base = Path(c).name
                hits = by_base.get(base)
                if hits:
                    # Deterministic: if multiple, take first in sorted order
                    picked = sorted(hits)[0]
                    break

        if picked is None:
            print(f"WARNING: requested entry not found in zip: {token}", file=sys.stderr)
            continue

        if picked in seen:
            continue
        seen.add(picked)
        selected.append(picked)

    return selected


def _convert_one_bcif(
    bcif_path: Path,
    working_cif_path: Path,
    cif_path: Path | None,
    pdb_path: Path | None,
    structure_id: str,
) -> None:
    if gemmi is None:
        raise RuntimeError("gemmi is required to convert AlphaFold BCIF files")

    _run_molstar_bcif_to_cif(bcif_path, working_cif_path)

    structure = gemmi.read_structure(str(working_cif_path), format=gemmi.CoorFormat.Detect)
    structure.name = structure_id

    atom_count = _count_atoms(structure)
    if atom_count <= 0:
        raise RuntimeError("converted_structure_has_no_atoms")

    if cif_path is not None:
        shutil.copyfile(working_cif_path, cif_path)

    if pdb_path is not None:
        structure.write_pdb(str(pdb_path))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a zip of .bcif files into two zips: one containing .cif files and one containing .pdb files."
        )
    )
    parser.add_argument("--bcif-zip", required=True, help="Input zip containing .bcif files")
    parser.add_argument(
        "--list-file",
        default=None,
        help=(
            "Optional file listing entries/IDs to process (one per line). "
            "Lines may be either 'AF-...-model_vN' or 'AF-...-model_vN.bcif' or full zip member names."
        ),
    )
    parser.add_argument("--out-cif-zip", required=False, help="Output zip containing .cif files")
    parser.add_argument("--out-pdb-zip", required=False, help="Output zip containing .pdb files")
    args = parser.parse_args()

    bcif_zip_path = Path(args.bcif_zip)
    list_file_path = Path(args.list_file) if args.list_file else None
    out_cif_zip = Path(args.out_cif_zip) if args.out_cif_zip else None
    out_pdb_zip = Path(args.out_pdb_zip) if args.out_pdb_zip else None

    if out_cif_zip is None and out_pdb_zip is None:
        raise SystemExit("At least one of --out-cif-zip or --out-pdb-zip must be provided")

    requested = _load_list_file(list_file_path)

    with zipfile.ZipFile(bcif_zip_path, "r") as zf:
        members = [n for n in zf.namelist() if not n.endswith("/") and n.lower().endswith(".bcif")]
        to_process = _select_members(members, requested)

        if not to_process:
            raise SystemExit("No BCIF entries selected to process")

        if out_cif_zip is not None:
            out_cif_zip.parent.mkdir(parents=True, exist_ok=True)
        if out_pdb_zip is not None:
            out_pdb_zip.parent.mkdir(parents=True, exist_ok=True)

        converted = 0
        failed = 0

        with ExitStack() as stack:
            cif_z = (
                stack.enter_context(zipfile.ZipFile(out_cif_zip, "w", compression=zipfile.ZIP_DEFLATED))
                if out_cif_zip is not None
                else None
            )
            pdb_z = (
                stack.enter_context(zipfile.ZipFile(out_pdb_zip, "w", compression=zipfile.ZIP_DEFLATED))
                if out_pdb_zip is not None
                else None
            )
            tmpdir = stack.enter_context(tempfile.TemporaryDirectory(prefix="bcif_convert_"))
            tmp = Path(tmpdir)

            for member in to_process:
                base = Path(member).name
                stem = base[:-5]  # drop .bcif

                cif_name = _safe_arcname(stem, ".cif") if cif_z is not None else None
                pdb_name = _safe_arcname(stem, ".pdb") if pdb_z is not None else None

                try:
                    bcif_path = tmp / _safe_arcname(stem, ".bcif")
                    working_cif_path = tmp / _safe_arcname(f"{stem}_molstar", ".cif")

                    # Stream member to disk (avoid path traversal issues)
                    with zf.open(member, "r") as src, bcif_path.open("wb") as dst:
                        while True:
                            chunk = src.read(1024 * 1024)
                            if not chunk:
                                break
                            dst.write(chunk)

                    cif_path = (tmp / cif_name) if cif_name is not None else None
                    pdb_path = (tmp / pdb_name) if pdb_name is not None else None

                    _convert_one_bcif(bcif_path, working_cif_path, cif_path, pdb_path, structure_id=stem)

                    wrote_any = False

                    if cif_z is not None and cif_path is not None:
                        if not cif_path.exists() or cif_path.stat().st_size == 0:
                            raise RuntimeError("cif_missing_or_empty")
                        cif_z.write(cif_path, arcname=cif_name)
                        wrote_any = True

                    if pdb_z is not None and pdb_path is not None:
                        if not pdb_path.exists() or pdb_path.stat().st_size == 0:
                            raise RuntimeError("pdb_missing_or_empty")
                        pdb_z.write(pdb_path, arcname=pdb_name)
                        wrote_any = True

                    if not wrote_any:
                        raise RuntimeError("no_outputs_requested")

                    converted += 1

                except Exception as e:
                    failed += 1
                    print(f"WARNING: failed converting {member}: {type(e).__name__}: {e}", file=sys.stderr)

        if converted == 0:
            raise SystemExit("No files were successfully converted")

        print(f"Converted: {converted}; Failed: {failed}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
