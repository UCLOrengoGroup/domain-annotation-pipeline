#!/usr/bin/env python3

import os
import argparse
from collections import defaultdict

# Usage:
# python3 chunk_consensus_by_zip.py \
#   --consensus_file  output from consensus chopping channel \
#   --chunk_size      numeric light_chunk_size \
#   --outdir          directory for output file \
#   --file_list       light_chunk_mapping.tsv

parser = argparse.ArgumentParser()

parser.add_argument("--consensus_file", required=True)
parser.add_argument("--chunk_size", type=int, required=True)
parser.add_argument("--outdir", required=True)
parser.add_argument("--file_list", required=True)

args = parser.parse_args()


consensus_file = args.consensus_file
chunk_size = args.chunk_size
outdir = args.outdir
file_list = args.file_list

# Make sure the output directory exists.
os.makedirs(outdir, exist_ok=True)
rows_by_zip = defaultdict(list)

# Input rows are:
# consensus_col1<TAB>consensus_col2<...><TAB>zip_name
with open(args.consensus_file) as f:
    for line in f:
        line = line.rstrip("\n")
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) < 2:
            raise ValueError(f"Invalid consensus_file row: {line}")
        zip_name = fields[-1]
        consensus_row = "\t".join(fields[:-1])
        rows_by_zip[zip_name].append(consensus_row)
chunk_id = 0
with open(args.file_list, "w") as mapping:
    mapping.write("chunk_id\tchunk_file\tzip_name\n")

    for zip_name in sorted(rows_by_zip):
        rows = rows_by_zip[zip_name]

        zip_stem = os.path.basename(zip_name).replace(".zip", "")

        for start in range(0, len(rows), args.chunk_size):
            chunk_rows = rows[start:start + args.chunk_size]

            chunk_file = f"{args.outdir}/{zip_stem}_consensus_chunks.{chunk_id}.tsv"

            with open(chunk_file, "w") as out:
                for row in chunk_rows:
                    out.write(row + "\n")

            mapping.write(f"{chunk_id}\t{chunk_file}\t{zip_name}\n")
            chunk_id += 1
