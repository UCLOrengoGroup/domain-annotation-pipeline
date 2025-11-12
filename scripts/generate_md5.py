#!/usr/bin/env python3
import sys
import os
from Bio.PDB import PDBParser
sys.path.append('/cath-alphaflow')
from cath_alphaflow.seq_utils import biostructure_to_md5

if len(sys.argv) < 2:
    print("Usage: generate_md5.py <input_pdb_file>")
    sys.exit(1)

pdb_file = sys.argv[1]
base_name = os.path.basename(pdb_file)
out_file = f"md5_{base_name.replace('.pdb', '')}.tsv"

parser = PDBParser(QUIET=True)
structure = parser.get_structure("x", pdb_file)
md5 = biostructure_to_md5(structure)

# --- write legacy-compatible output ---
with open(out_file, "w") as out:
    out.write("pdb_file\tchain\tmd5\tsequence\n")
    out.write(f"{base_name}\tA\t{md5}\tNA\n")
