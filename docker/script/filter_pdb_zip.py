#!/usr/bin/env python3
"""Validate and filter single-chain PDB files stored in a ZIP archive.

Two outputs are produced: a plain list of accepted IDs and a TSV manifest with
validation metadata for every requested structure. Residue counts include only
amino-acid residues, so accepted rows can also drive length-aware chunking.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from pathlib import Path
import sys
import zipfile

import gemmi


STANDARD_AMINO_ACIDS = frozenset(
    "ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL".split()
)

# Merizo converts these names to standard amino acids. Keep this list aligned
# with SPECIAL_AA in ted-tools/programs/merizo/model/utils/build_info.py.
TED_MODIFIED_AMINO_ACIDS = frozenset("MSE SEC CSD PCA PYL".split())
TED_SUPPORTED_AMINO_ACIDS = STANDARD_AMINO_ACIDS | TED_MODIFIED_AMINO_ACIDS
AMBIGUOUS_AMINO_ACIDS = frozenset("ASX GLX UNK".split())


@dataclass
class ValidationResult:
    """One row in the validation manifest."""

    pdb_id: str
    zip_name: str
    status: str = "rejected"
    reason: str = ""
    model_count: int | None = None
    chain_count: int | None = None
    chain_ids: str = ""
    residue_count: int | None = None
    missing_ca_count: int | None = None
    unsupported_residue_names: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Filter zipped PDB files and write a validation manifest."
    )
    parser.add_argument("--pdb-zip", required=True, type=Path)
    parser.add_argument("--ids", required=True, type=Path)
    parser.add_argument("--min-residues", required=True, type=int)
    parser.add_argument("--max-residues", required=True, type=int)
    parser.add_argument("--output-ids", required=True, type=Path)
    parser.add_argument("--output-metadata", required=True, type=Path)
    return parser.parse_args()


def is_amino_acid(residue: gemmi.Residue) -> bool:
    """Return whether Gemmi recognises a residue as an amino acid."""

    return (
        gemmi.find_tabulated_residue(residue.name).is_amino_acid()
        or residue.name in AMBIGUOUS_AMINO_ACIDS
    )


def validate_pdb(
    pdb_id: str,
    zip_name: str,
    pdb_text: str,
    min_residues: int,
    max_residues: int,
) -> ValidationResult:
    """Validate one PDB and return its metadata and acceptance decision."""

    result = ValidationResult(pdb_id=pdb_id, zip_name=zip_name)
    try:
        structure = gemmi.read_pdb_string(pdb_text)
    except Exception as exc:  # Gemmi exposes several parser exception types.
        result.reason = f"could not parse PDB: {exc}"
        return result

    result.model_count = len(structure)
    if result.model_count != 1:
        result.reason = f"expected one model, found {result.model_count}"
        return result

    model = structure[0]
    result.chain_count = len(model)
    result.chain_ids = ",".join(chain.name for chain in model)
    if result.chain_count != 1:
        result.reason = f"expected one chain, found {result.chain_count}"
        return result

    amino_acids = [residue for residue in model[0] if is_amino_acid(residue)]
    result.residue_count = len(amino_acids)
    if not amino_acids:
        result.reason = "no amino-acid residues"
        return result

    unsupported = sorted(
        {residue.name for residue in amino_acids if residue.name not in TED_SUPPORTED_AMINO_ACIDS}
    )
    result.unsupported_residue_names = ",".join(unsupported)
    if unsupported:
        result.reason = "unsupported amino-acid residues: " + ", ".join(unsupported)
        return result

    result.missing_ca_count = sum(
        not any(atom.name.strip() == "CA" for atom in residue)
        for residue in amino_acids
    )
    if result.missing_ca_count:
        result.reason = f"{result.missing_ca_count} amino-acid residue(s) have no CA atom"
        return result

    if result.residue_count <= min_residues:
        result.reason = f"not more than {min_residues} residues"
        return result

    if result.residue_count >= max_residues:
        result.reason = f"at least {max_residues} residues"
        return result

    result.status = "accepted"
    return result


def read_ids(path: Path) -> list[str]:
    """Read non-empty IDs while preserving input order."""

    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def main() -> int:
    args = parse_args()
    if args.min_residues >= args.max_residues:
        raise ValueError("--min-residues must be less than --max-residues")

    results: list[ValidationResult] = []
    accepted_ids: list[str] = []

    with zipfile.ZipFile(args.pdb_zip) as pdb_zip:
        members = {Path(name).name: name for name in pdb_zip.namelist()}
        for pdb_id in read_ids(args.ids):
            pdb_name = f"{pdb_id}.pdb"
            if pdb_name not in members:
                result = ValidationResult(
                    pdb_id=pdb_id,
                    zip_name=args.pdb_zip.name,
                    reason=f"{pdb_name} not found in ZIP archive",
                )
            else:
                try:
                    pdb_text = pdb_zip.read(members[pdb_name]).decode("utf-8")
                except (OSError, UnicodeDecodeError) as exc:
                    result = ValidationResult(
                        pdb_id=pdb_id,
                        zip_name=args.pdb_zip.name,
                        reason=f"could not read PDB: {exc}",
                    )
                else:
                    result = validate_pdb(
                        pdb_id,
                        args.pdb_zip.name,
                        pdb_text,
                        args.min_residues,
                        args.max_residues,
                    )

            results.append(result)
            if result.status == "accepted":
                accepted_ids.append(pdb_id)
            else:
                print(f"WARNING: skipping {pdb_name}: {result.reason}", file=sys.stderr)

    args.output_ids.write_text("".join(f"{pdb_id}\n" for pdb_id in accepted_ids))
    with args.output_metadata.open("w", newline="") as metadata_file:
        fieldnames = list(asdict(ValidationResult("", "")).keys())
        writer = csv.DictWriter(
            metadata_file,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(asdict(result) for result in results)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
