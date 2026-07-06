#!/usr/bin/env python3

import os
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

# Read all IDs and group them by zip file
ids_by_zip = defaultdict(list)

with open(input_file) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        pdb_id, zip_name = line.split("\t")
        ids_by_zip[zip_name].append(pdb_id)

# Write chunk files and file_list
chunk_id = 0

with open(file_list, "w") as mapping:
    mapping.write("chunk_id\tchunk_file\tzip_name\n")

    for zip_name in sorted(ids_by_zip):
        ids = sorted(set(ids_by_zip[zip_name]))

        for start in range(0, len(ids), chunk_size):
            chunk_ids = ids[start:start + chunk_size]

            zip_stem = os.path.basename(zip_name).replace(".zip", "")
            chunk_file = f"{outdir}/{zip_stem}_ids_mapping.{chunk_id}.txt"

            with open(chunk_file, "w") as out:
                for pdb_id in chunk_ids:
                    out.write(pdb_id + "\n")

            mapping.write(f"{chunk_id}\t{chunk_file}\t{zip_name}\n")
            chunk_id += 1
