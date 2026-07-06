#!/usr/bin/env python3

import os
import argparse
import zipfile

# Usage:
# python3 create_input_from_zip_script.py \
#    --input_zip_dir    input_zip_dir \
#    --output           output file \

parser = argparse.ArgumentParser()

parser.add_argument("--input_zip_dir",  required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

with open(args.output, "w") as out:
    for zip_name in sorted(os.listdir(args.input_zip_dir)):     # Create sorted list of zips in the directory.
        if not zip_name.endswith(".zip"):                       # Skip anything that is not a .zip file.
            continue
        zip_path = os.path.join(args.input_zip_dir, zip_name)   # Build a path to zip (/data/zips/bfvd_zip1.zip)
        with zipfile.ZipFile(zip_path) as z:                    # Open the zip file without extracting it.
            for member in sorted(z.namelist()):                 # Get a sorted list of contents in each zip file.
                if member.endswith((".pdb", ".cif")):           # Skip anything that's not a pdb or cif file.
                    file_id = os.path.basename(member)[:-4]     # Remove the .pdb/.cif suffix.
                    out.write(f"{file_id}\t{zip_name}\n")       # Write names to a tsv file.
