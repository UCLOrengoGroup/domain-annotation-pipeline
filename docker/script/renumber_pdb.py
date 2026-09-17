import csv
import gemmi
import sys
import argparse
import tempfile
import zipfile
from pathlib import Path

# Define a function to renumber the file.
def renumber_pdb(input_file, output_file, mapping_file):
    # Input the pdb into gemmi
    st = gemmi.read_structure(str(input_file))
    # A PDB with no models cannot be processed
    if len(st) == 0:
        raise ValueError(f"Failed to find any models in PDB {input_file}")

    # If multiple models are present, continue using only the first model
    if len(st) > 1:
        print(f"WARNING: Found {len(st)} models in PDB {input_file}, only the first model will be used.", flush=True)

    # Keep only model 1
    while len(st) > 1:
        del st[1]

    model = st[0]
    # Remove non-polymer residues such as ions, waters and ligands
    model.remove_ligands_and_waters()
    #model.remove_waters() # Replace the above line with this if we really want to keep ligands but later Gemmi logic may need updating.

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
parser = argparse.ArgumentParser(description="Normalise PDB residue numbering and create residue maps.")

parser.add_argument("--input_zip", required=True)
parser.add_argument("--id_file", required=True)
parser.add_argument("--normalised_zip", required=True)
parser.add_argument("--resmaps_zip", required=True)
parser.add_argument("--error_file", required=True)

args = parser.parse_args()

input_zip = args.input_zip
id_file = args.id_file
normalised_zip = args.normalised_zip
resmaps_zip = args.resmaps_zip
error_file = args.error_file

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

    errors = []
    for pdb_idx, pdb_id in enumerate(ids, start=1):
        if pdb_idx == 1 or pdb_idx % 100 == 0:
            print(f"Processing PDB {pdb_id} ({pdb_idx}/{len(ids)})", flush=True) # Add logging for pdb 1 and every 100
        pdb_name = pdb_id + ".pdb"
        # Extract the required PDB from the input ZIP
        input_pdb = temp_dir / pdb_name
        with input_zip_handle.open(pdb_name) as source:
            with open(input_pdb, "wb") as destination:
                destination.write(source.read())
        # Define output filenames
        normalised_pdb = temp_dir / f"{pdb_id}.pdb"
        mapping_file = temp_dir / f"{pdb_id}_resmap.tsv"

        # Call the renumber_pdb function and create its mapping file.
        # If this PDB cannot be processed, record the error and skip it.
        try:
            renumber_pdb(
                input_pdb,
                normalised_pdb,
                mapping_file)
        except Exception as e:
            print(f"WARNING: Failed to process {pdb_name}: {e} (skipping)", flush=True)
            errors.append((pdb_name, str(e)))
            continue
        # Add outputs to their ZIP files
        normalised_zip_handle.write(
            normalised_pdb,
            normalised_pdb.name)

        resmaps_zip_handle.write(
            mapping_file,
            mapping_file.name)

    # Write a report of any PDBs that could not be processed
    with open(error_file, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["pdb_file", "error"])
        writer.writerows(errors)

    # Close all files
    input_zip_handle.close()
    normalised_zip_handle.close()
    resmaps_zip_handle.close()