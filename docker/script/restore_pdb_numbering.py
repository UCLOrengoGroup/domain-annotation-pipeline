import csv
import gemmi
import sys
from pathlib import Path

# Directories passed in from Nextflow
pdb_dir = Path(sys.argv[1])
resmap_dir = Path(sys.argv[2])

# Read each chopped PDB
for pdb_file in pdb_dir.glob("*.pdb"):
    # Get the original PDB ID from the chopped PDB name. e.g. A0A000_01.pdb -> A0A000
    pdb_id = pdb_file.stem.rsplit("_", 1)[0]

    # Find the corresponding residue mapping.
    mapping_file = resmap_dir / f"{pdb_id}_resmap.tsv"

    if not mapping_file.exists():
        raise ValueError(
            f"No residue mapping found for {pdb_file.name}")

    # Read the residue mapping
    residue_mapping = {}

    with open(mapping_file) as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            new_resnum = int(row["new_resnum"])
            original_resnum = int(row["original_resnum"])
            original_icode = row["original_icode"]
            original_chain = row["original_chain"]

            residue_mapping[new_resnum] = (
                original_resnum,
                original_icode,
                original_chain)

    # Read the chopped PDB and take the first (only) model
    st = gemmi.read_structure(str(pdb_file))
    model = st[0]
    # The chopped PDB should contain one chain
    if len(model) != 1:
        raise ValueError(
            f"Expected one chain in {pdb_file}, found {len(model)}")
    chain = model[0]

    # Restore the original residue numbers
    for residue in chain:
        new_resnum = residue.seqid.num
        if new_resnum not in residue_mapping:
            raise ValueError(
                f"Residue {new_resnum} in {pdb_file.name} "
                f"was not found in {mapping_file.name}")

        original_resnum, original_icode, original_chain = \
            residue_mapping[new_resnum]

        # Restore original residue number, insertion code and chain name
        residue.seqid = gemmi.SeqId(
            original_resnum,
            original_icode if original_icode else " ")

    chain.name = original_chain

    # Overwrite the chopped PDB with the restored version
    st.write_pdb(str(pdb_file))