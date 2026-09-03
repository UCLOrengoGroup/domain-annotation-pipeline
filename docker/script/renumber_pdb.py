import csv
import gemmi
import sys
import tempfile
import zipfile
from pathlib import Path

# Define a function to renumber the file.
def renumber_pdb(input_file, output_file, mapping_file):
    # Input the pdb into emmi
    st = gemmi.read_structure(str(input_file))
    # Keep only model 1 (just incase NMR files contain multiple)
    while len(st) > 1:
        del st[1]
    model = st[0]
    # Remove non-polymer residues such as ions, waters and ligands
    model.remove_ligands_and_waters()
    # Only single-chain structures are allowed
    if len(model) != 1:
        raise ValueError(
            f"Expected one chain in {input_file}, found {len(model)}")
    # Keep the first chain in the model (0)
    chain = model[0]
    # Define the original chain name to use later and rename the chain to A
    original_chain = chain.name
    chain.name = "A"
    # Create/open a mapping file
    mapping = open(mapping_file, "w", newline="")
    writer = csv.writer(mapping, delimiter="\t")
    writer.writerow([
        "pdb_file",
        "new_chain",
        "new_resnum",
        "original_chain",
        "original_resnum",
        "original_icode"])
    # Set a counter to 1
    residue_counter = 1
    for residue in chain:
        # Save original numbering before changing it
        original_resnum = residue.seqid.num
        original_icode = residue.seqid.icode.strip()
        # Write the mapping file data
        writer.writerow([
            Path(input_file).name,
            "A",
            residue_counter,
            original_chain,
            original_resnum,
            original_icode])
        # Now renumber the residues
        residue.seqid = gemmi.SeqId(residue_counter, " ")
        residue_counter += 1
    # Close the mapping file
    mapping.close()
    # Write the newly renumbered residues to the output pdb file.
    st.write_pdb(str(output_file))

# Values passed in/out from Nextflow
input_zip = sys.argv[1]
id_file = sys.argv[2]
normalised_zip = sys.argv[3]
resmaps_zip = sys.argv[4]

# Read the IDs required for this chunk
ids = []
with open(id_file) as f:
    for line in f:
        line = line.strip()
        if line:
            ids.append(line)
# Temporary directory for extracted and converted files
with tempfile.TemporaryDirectory() as temp_dir:
    temp_dir = Path(temp_dir)
    # Open input ZIP and the two output ZIPs
    input_zip_handle = zipfile.ZipFile(input_zip, "r")
    normalised_zip_handle = zipfile.ZipFile(
        normalised_zip, "w", zipfile.ZIP_DEFLATED)
    resmaps_zip_handle = zipfile.ZipFile(
        resmaps_zip, "w", zipfile.ZIP_DEFLATED)
    for pdb_id in ids:
        pdb_name = pdb_id + ".pdb"
        # Extract the required PDB from the input ZIP
        input_pdb = temp_dir / pdb_name
        with input_zip_handle.open(pdb_name) as source:
            with open(input_pdb, "wb") as destination:
                destination.write(source.read())
        # Define output filenames
        normalised_pdb = temp_dir / f"{pdb_id}.pdb"
        mapping_file = temp_dir / f"{pdb_id}_resmap.tsv"

        # Call the renumber_pdb function and create its mapping file
        renumber_pdb(
            input_pdb,
            normalised_pdb,
            mapping_file)
        # Add outputs to their ZIP files
        normalised_zip_handle.write(
            normalised_pdb,
            normalised_pdb.name)

        resmaps_zip_handle.write(
            mapping_file,
            mapping_file.name)
    # Close all files
    input_zip_handle.close()
    normalised_zip_handle.close()
    resmaps_zip_handle.close()