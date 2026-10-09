#!/usr/bin/env python3
#-------------------------------------------------------------------------------------
# This script is used by chunk_by_zipfile.nf in two distinct places in the workflow.
#
# FIRST PASS: aliased as chunk_by_zip
# -----------------------------------
# Assigns params.chunk_size, input rows are normally: <pdb_id> <zip_name> from all_ids_mapping.txt
# Behaviour:
# 1. Group the incoming <pdb_id> and <zip_name> alphabetically by parent ZIP (zip_name)
# 2. Sort the PDB IDs from each individual ZIP alphabetically
# 3. Write them to a series of chunk files named chunks/<zip_name>_ids_mapping.X.zip (X is 0 -> n) with chunk_size rows
#    e.g. inside zip_name_mapping.0.txt, PDB IDs will be arranged as: PDB1, PDB2, PDB3..etc
# 4. Create a master file called chunk_mapping.tsv containing the following data:
#    chunk_id    chunk_file                              zip_name
#    0           /path/chunks/zip_name_mapping.0.txt     zip_name.zip
#
# SECOND PASS: aliased as heavy_chunk_by_zip
# -------------------------------------------
# Assigns params.heavy_chunk_size after PDB filtering. Input rows: <pdb_id> <zip_name> <residue_count> from filtered_af_ids.txt
# Behaviour:
# 1. Group the incoming <pdb_id> <zip_name> <residue_count> alphabetically by parent ZIP (zip_name)
#    If experimental=true (normalised_XX.zip), zip files are sorted numerically (by XX) instead
# 2. This time sort the PDB IDs from each individual ZIP numerically (highest -> lowest) by residue_count
# 3. Write them to a series of chunk files named chunks/<zip_name>_ids_mapping.X.zip with heavy_chunk_size rows
#    e.g. inside zip_name_mapping.0.txt, PDB IDs will be arranged as: PDB3 120, PDB2 100, PDB1 90..etc
# 4. Create the same master file called chunk_mapping.tsv
# Reverse sorting of PDB IDs within chunks is to ensure chunk failure due to length-associated memory will happen immediately
#--------------------------------------------------------------------------------------
import os
import re
import argparse
from collections import defaultdict

# Usage:
# python3 chunk_by_zip.py \
#    --input_file   txt file containing pdb id and zip file name \
#    --chunk_size   numeric chunk size \
#    --outdir       directory for output file \
#    --file_list    output mapping.tsv

parser = argparse.ArgumentParser()

parser.add_argument("--input_file", required=True)            # file containing pdb_id, zip_name (and residue_count)
parser.add_argument("--chunk_size", type=int, required=True)  # numeric chunk size (params.chunk_size or heavy_chunk_size)
parser.add_argument("--outdir", required=True)                # output directory (PWD/chunks)
parser.add_argument("--file_list", required=True)             # ouput filename (chunk_mapping.tsv)

args = parser.parse_args()

input_file = args.input_file
chunk_size = args.chunk_size
outdir = args.outdir
file_list = args.file_list

os.makedirs(outdir, exist_ok=True)

# Read all IDs and group them by zip file in a dictionary ("ABCD.zip": {"A0A000_01": 80}. The third column is optional; when
# present it is the residue count emitted by filter_pdb_zip.py. If residue counts are not supplied, values will be None.
ids_by_zip = defaultdict(dict)

with open(input_file) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        fields = line.split("\t")                             # fields[0]="A0A000_01", fields[1]="ABCD.zip", fields[2]=80 or None
        if len(fields) not in (2, 3):                         # Only 2-column or 3-column input is allowed or error
            raise ValueError(
                f"Expected 2 or 3 tab-separated fields, found {len(fields)}: {line}"
            )

        pdb_id, zip_name = fields[:2]
        residue_count = int(fields[2]) if len(fields) == 3 else None
        ids_by_zip[zip_name][pdb_id] = residue_count

# If ZIP files are named normalised_XX.zip, sort them by the number (XX) to maintain provenance between the heavy chunk number 
# and the original chunk number (this is vital for experimental PDBs). Otherwise, retain alphabetic sorting for predicted models.
# For first pass (chunk_by_zip) it will always be alphabetic sorting.
normalised_pattern = re.compile(r"normalised_(\d+)\.zip$")

all_normalised = all(
    normalised_pattern.fullmatch(os.path.basename(zip_name))
    for zip_name in ids_by_zip)

if all_normalised:
    zip_names = sorted(
        ids_by_zip,
        key=lambda zip_name: int(
            normalised_pattern.fullmatch(
                os.path.basename(zip_name)
            ).group(1)))
else:
    zip_names = sorted(ids_by_zip)

# Write chunk files and file_list (chunk_mapping.tsv)
chunk_id = 0                                # First chunk will always be numbered 0

with open(file_list, "w") as mapping:
    mapping.write("chunk_id\tchunk_file\tzip_name\tmax_residues\n")

    for zip_name in zip_names:
        ids_with_lengths = ids_by_zip[zip_name]
        # define the variable has_lengths to show where residue_counts are known in all cases
        has_lengths = all(length is not None for length in ids_with_lengths.values())
        if has_lengths:
            ids = sorted(
                ids_with_lengths,
                key=lambda pdb_id: (ids_with_lengths[pdb_id], pdb_id),
            )
        else:
            ids = sorted(ids_with_lengths)

        for start in range(0, len(ids), chunk_size):
            chunk_ids = ids[start:start + chunk_size]
            max_residues = ""
            # use has_lengths to order pdb ids in reverse numerical order within chunks
            if has_lengths:
                chunk_ids = sorted(chunk_ids, key=lambda pdb_id: (-ids_with_lengths[pdb_id], pdb_id))
                max_residues = max(ids_with_lengths[pdb_id] for pdb_id in chunk_ids)

            zip_stem = os.path.basename(zip_name).replace(".zip", "")
            chunk_file = f"{outdir}/{zip_stem}_ids_mapping.{chunk_id}.txt"

            with open(chunk_file, "w") as out:
                for pdb_id in chunk_ids:
                    out.write(pdb_id + "\n")

            mapping.write(f"{chunk_id}\t{chunk_file}\t{zip_name}\t{max_residues}\n")
            chunk_id += 1
