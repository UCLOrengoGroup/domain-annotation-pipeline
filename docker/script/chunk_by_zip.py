#!/usr/bin/env python3

import sys
import os
from collections import defaultdict

# Usage:
# python3 chunk_by_zip.py all_af_ids.txt "chunk_size" chunks chunk_mapping.tsv (chunk_size must be a number)

input_file = sys.argv[1]
chunk_size = int(sys.argv[2])
outdir = sys.argv[3]
file_list = sys.argv[4]

os.makedirs(outdir, exist_ok=True)

# Read all IDs and group them by zip file
ids_by_zip = defaultdict(list)

with open(input_file) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        pdb_id, zip_file = line.split("\t")
        ids_by_zip[zip_file].append(pdb_id)

# Write chunk files and file_list
chunk_id = 0

with open(file_list, "w") as mapping:
    mapping.write("chunk_id\tchunk_file\tzip_file\n")

    for zip_file in sorted(ids_by_zip):
        ids = sorted(set(ids_by_zip[zip_file]))

        for start in range(0, len(ids), chunk_size):
            chunk_ids = ids[start:start + chunk_size]

            zip_name = os.path.basename(zip_file).replace(".zip", "")
            chunk_file = f"{outdir}/{zip_name}_af_ids.{chunk_id}.txt"

            with open(chunk_file, "w") as out:
                for pdb_id in chunk_ids:
                    out.write(pdb_id + "\n")

            mapping.write(f"{chunk_id}\t{chunk_file}\t{zip_file}\n")
            chunk_id += 1
