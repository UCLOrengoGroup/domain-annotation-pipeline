#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path

def load_resmaps(resmap_dir):
    """Load all residue maps, indexed by PDB ID and new residue number."""
    mappings = {}

    for resmap_file in Path(resmap_dir).glob("*_resmap.tsv"):
        pdb_id = resmap_file.name.replace("_resmap.tsv", "")
        residue_map = {}

        with resmap_file.open(newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")

            for row in reader:
                new_resnum = int(row["new_resnum"])
                original_resnum = row["original_resnum"].strip()
                original_icode = row["original_icode"].strip()

                # Preserve insertion codes, e.g. residue 100 + icode A -> 100A
                original_label = f"{original_resnum}{original_icode}"

                residue_map[new_resnum] = original_label

        mappings[pdb_id] = residue_map
    return mappings

def restore_chopping(chopping, residue_map):
    """Convert normalised chopping coordinates back to original numbering."""
    restored_segments = []
    for segment in chopping.split("_"):
        if "-" in segment:
            start, end = segment.split("-", 1)

            start = int(start)
            end = int(end)

            if start not in residue_map:
                raise ValueError(f"Normalised residue {start} not found in residue map")

            if end not in residue_map:
                raise ValueError(f"Normalised residue {end} not found in residue map")

            restored_segments.append(f"{residue_map[start]}-{residue_map[end]}")

        else:
            residue = int(segment)

            if residue not in residue_map:
                raise ValueError(f"Normalised residue {residue} not found in residue map")

            restored_segments.append(residue_map[residue])

    return "_".join(restored_segments)


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Restore original PDB residue numbering in the chopping column "
            "of final_results.tsv."))

    parser.add_argument("--final_results", required=True)
    parser.add_argument("--resmap_dir", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    mappings = load_resmaps(args.resmap_dir)

    with open(args.final_results, newline="") as infile, \
            open(args.output, "w", newline="") as outfile:

        reader = csv.DictReader(infile, delimiter="\t")

        writer = csv.DictWriter(
            outfile,
            fieldnames=reader.fieldnames,
            delimiter="\t",
            lineterminator="\n")

        writer.writeheader()

        for row in reader:

            # 1AZZ_01 -> 1AZZ
            pdb_id = row["uniprot_id"].rsplit("_", 1)[0]

            if pdb_id not in mappings:
                raise ValueError(
                    f"No residue map found for {pdb_id}")

            row["chopping"] = restore_chopping(
                row["chopping"],
                mappings[pdb_id])

            writer.writerow(row)

if __name__ == "__main__":
    main()