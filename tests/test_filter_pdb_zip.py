"""Unit tests for the PDB validation policy used before TED segmentation."""

import importlib.util
from pathlib import Path
import sys
import unittest


SCRIPT = Path(__file__).parents[1] / "docker" / "script" / "filter_pdb_zip.py"
SPEC = importlib.util.spec_from_file_location("filter_pdb_zip", SCRIPT)
filter_pdb_zip = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = filter_pdb_zip
SPEC.loader.exec_module(filter_pdb_zip)


def atom_line(serial, atom_name, residue_name, residue_number):
    """Return one fixed-width PDB ATOM record."""

    return (
        f"ATOM  {serial:5d} {atom_name:^4s} {residue_name:>3s} A{residue_number:4d}    "
        "   0.000   0.000   0.000  1.00  0.00           C\n"
    )


def pdb_with_residues(residues):
    lines = []
    serial = 1
    for residue_number, (residue_name, atom_names) in enumerate(residues, start=1):
        for atom_name in atom_names:
            lines.append(atom_line(serial, atom_name, residue_name, residue_number))
            serial += 1
    return "".join(lines) + "TER\nEND\n"


class ValidatePdbTests(unittest.TestCase):
    def validate(self, residues):
        return filter_pdb_zip.validate_pdb(
            "test", "structures.zip", pdb_with_residues(residues), 0, 10
        )

    def test_accepts_supported_residues_with_ca_atoms(self):
        result = self.validate([
            ("ALA", ("N", "CA", "C", "O")),
            ("MSE", ("N", "CA", "C", "O")),
        ])

        self.assertEqual(result.status, "accepted")
        self.assertEqual(result.chain_ids, "A")
        self.assertEqual(result.residue_count, 2)

    def test_rejects_ambiguous_residues(self):
        result = self.validate([("UNK", ("N", "CA", "C", "O"))])

        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.unsupported_residue_names, "UNK")

    def test_rejects_residue_without_ca_atom(self):
        result = self.validate([("ALA", ("N", "C", "O"))])

        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.missing_ca_count, 1)


if __name__ == "__main__":
    unittest.main()
