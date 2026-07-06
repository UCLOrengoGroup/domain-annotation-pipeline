#!/usr/bin/env python3
# modified to output header line which can be referred to by transform_consensus.py
import sys
import os
import hashlib
from Bio.PDB import PDBParser, PPBuilder
from io import StringIO

def get_sequence_from_pdb(pdb_file, chain_id=None):
    parser = PDBParser(QUIET=True)

    with open(pdb_file, "r") as f:
        lines = f.readlines()

    # Keep MODEL/ENDMDL only if they are at the start or end — remove others
    cleaned_lines = []
    for i, line in enumerate(lines):
        if line.startswith("MODEL") or line.startswith("ENDMDL"):
            if i == 0 or i == len(lines) - 1:
                cleaned_lines.append(line)
            else:
                continue
        else:
            cleaned_lines.append(line)

    pdb_string = "".join(cleaned_lines)
    structure = parser.get_structure("PDB_structure", StringIO(pdb_string))
    ppb = PPBuilder()

    for model in structure:
        for chain in model:
            if chain_id and chain.id != chain_id:
                continue
            peptides = ppb.build_peptides(chain)
            full_sequence = "".join(str(peptide.get_sequence()) for peptide in peptides)
            return full_sequence
    return ""

def md5_of_sequence(sequence: str) -> str:
    cleaned_seq = sequence.strip().upper()
    return hashlib.md5(cleaned_seq.encode('utf-8')).hexdigest()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: pdb_to_md5.py <input_pdb_file> <output_tsv_file> [chain_id]")
        sys.exit(1)

    pdb_file = sys.argv[1]
    output_file = sys.argv[2]
    chain = sys.argv[3] if len(sys.argv) > 3 else "A"

    seq = get_sequence_from_pdb(pdb_file, chain_id=chain)

    with open(output_file, "w") as out:
        out.write("pdb_file\tchain\tmd5\tsequence\n")
        if seq:
            md5 = md5_of_sequence(seq)
            out.write(f"{os.path.basename(pdb_file)}\t{chain}\t{md5}\t{seq}\n")
        else:
            out.write(f"{os.path.basename(pdb_file)}\t{chain}\tNA\tNo sequence found\n")
