#!/usr/bin/env python3

import os
import re
import argparse
from collections import defaultdict

# Usage:
# python3 chunk_by_zip.py \
#    --input_file   tsv file containing pdb id and zip file name \
#    --chunk_size   numeric chunk size \
#    --outdir       directory for output file \
#    --file_list    output mapping.tsv

parser = argparse.ArgumentParser()

parser.add_argument("--input_file", required=True)
parser.add_argument("--chunk_size", type=int, required=True)
parser.add_argument("--outdir", required=True)
parser.add_argument("--file_list", required=True)

args = parser.parse_args()

input_file = args.input_file
chunk_size = args.chunk_size
outdir = args.outdir
file_list = args.file_list

os.makedirs(outdir, exist_ok=True)

# Read all IDs and group them by zip file. A third column is optional; when
# present it is the residue count emitted by filter_pdb_zip.py.
ids_by_zip = defaultdict(dict)

with open(input_file) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        fields = line.split("\t")
        if len(fields) not in (2, 3):
            raise ValueError(
                f"Expected 2 or 3 tab-separated fields, found {len(fields)}: {line}"
            )

        pdb_id, zip_name = fields[:2]
        residue_count = int(fields[2]) if len(fields) == 3 else None
        ids_by_zip[zip_name][pdb_id] = residue_count

# If all ZIPs are normalised_<number>.zip files, sort them by that number so the heavy chunk IDs remain aligned with the original
# chunk IDs. Otherwise retain the normal filename sort.
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

# Write chunk files and file_list
chunk_id = 0

with open(file_list, "w") as mapping:
    mapping.write("chunk_id\tchunk_file\tzip_name\n")

    for zip_name in zip_names:
        ids_with_lengths = ids_by_zip[zip_name]
        if all(length is not None for length in ids_with_lengths.values()):
            ids = sorted(
                ids_with_lengths,
                key=lambda pdb_id: (ids_with_lengths[pdb_id], pdb_id),
            )
        else:
            ids = sorted(ids_with_lengths)

        for start in range(0, len(ids), chunk_size):
            chunk_ids = ids[start:start + chunk_size]

            zip_stem = os.path.basename(zip_name).replace(".zip", "")
            chunk_file = f"{outdir}/{zip_stem}_ids_mapping.{chunk_id}.txt"

            with open(chunk_file, "w") as out:
                for pdb_id in chunk_ids:
                    out.write(pdb_id + "\n")

            mapping.write(f"{chunk_id}\t{chunk_file}\t{zip_name}\n")
            chunk_id += 1
