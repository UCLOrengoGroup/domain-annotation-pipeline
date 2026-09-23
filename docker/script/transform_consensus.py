# Takes the information in filtered_consensus.tsv and transforms it from model-level to doamin level.
# Input cols: target_id', 'MD5', 'nres', 'high', 'med', 'low', 'high_dom', 'med_dom', 'low_dom'
# Output cols: ted_id', 'md5_domain', 'consensus_level', 'chopping', 'nres_domain', 'num_segments'
# Also parses STRIDE summary files (./results/stride), extracts the SSE fields and appends them to each row
# 23/5/25 - set MD5/md5_domain col to domain-level from md5_file to agree with globularity an plddt_and_lur programs.
# 27/5/25 - added error for non-existant md5 (line 72).
# Amended to read md5_file by named arguments rather than positional
# 19-Jun-25 - amended to omit "_dom" from domain names and "high" or "med" from filenames.
# 16-Sep-26 - added option '--warn-missing-stride-id' to allow warning for missing stride ids in summary files.
# 16-Sep-26 - memory / speed improvements: use CSV rather than pandas, stream output rather than loading entire file into memory.

import argparse
import csv
import os
import sys

DEFAULT_STRIDE_SUMMARY_SUFFIX = ".stride.summary"

parser = argparse.ArgumentParser(
    description="Transforms the consensus data.",
)

parser.add_argument(
    "--input_file",
    "-i",
    type=str,
    required=True,
    help="Path to the input file containing consensus data",
)
parser.add_argument(
    "--output_file",
    "-o",
    type=str,
    required=True,
    help="Path to the output file for transformed data",
)
parser.add_argument(
    "--md5_file",
    "-m",
    type=str,
    required=True,
    help="Path to the MD5 file for PDB files",
)
parser.add_argument(
    "--stride_dir",
    "-s",
    type=str,
    required=True,
    help="Path to STRIDE summary file directory",
)

parser.add_argument(
    "--stride_summary_suffix",
    type=str,
    default=DEFAULT_STRIDE_SUMMARY_SUFFIX,
    help="Suffix for STRIDE summary files (default: .stride.summary)",
)

parser.add_argument(
    "--warn-missing-stride-id",
    action="store_true",
    default=False,
    help="Warn if STRIDE ids in summary files are missing (default: throw error)",
)


def read_md5_file(md5_file):
    md5_lookup = {}
    with open(md5_file, newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        missing = {"pdb_file", "md5"} - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"MD5 file '{md5_file}' is missing columns: {sorted(missing)}")
        for row in reader:
            md5_lookup[row["pdb_file"]] = row["md5"]
    return md5_lookup


def parse_domain(domain):
    fragments = domain.split("_")
    total = 0
    min_start = None
    for frag in fragments:
        start, end = map(int, frag.split("-"))
        total += end - start + 1
        min_start = start if min_start is None else min(min_start, start)
    return total, len(fragments), min_start


def read_stride_summary(file_path, warn_missing_stride_id: bool=False):
    """
    Reads a STRIDE summary file (TSV) and returns tuples of required fields indexed by 'id'.
    """
    stride_data_by_id = dict()
    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError(f"Stride file '{file_path}' does not exist.")

    expected_keys = [
        "id",
        "chain_id",
        "num_helix_strand_turn",
        "num_helix",
        "num_strand",
        "num_helix_strand",
        "num_turn",
    ]

    with open(file_path, "r") as f:
        header = f.readline().rstrip("\n").split("\t")
        header_index = {name: idx for idx, name in enumerate(header)}
        missing_keys = set(expected_keys) - set(header)
        if missing_keys:
            raise ValueError(
                f"Missing keys {sorted(missing_keys)} in stride file: {file_path}"
            )
        unexpected_keys = set(header) - set(expected_keys)
        if unexpected_keys:
            raise ValueError(
                f"Unexpected keys {sorted(unexpected_keys)} in stride file: {file_path}"
            )
        line_count = 1
        for line in f:
            line_count += 1
            parts = line.rstrip("\n").split("\t")
            if len(parts) != len(header):
                raise ValueError(f"Invalid format in stride file: {file_path}, line {line_count}: {line.rstrip()}")

            stride_id = parts[header_index["id"]]
            if not stride_id:
                if warn_missing_stride_id:
                    print(f"WARNING: Missing 'id' in stride file: {file_path}, line {line_count}: {line.rstrip()} (ignoring)", file=sys.stderr)
                    continue
                else:
                    raise ValueError(f"Missing 'id' in stride file: {file_path}, line {line_count}: {line.rstrip()}")

            stride_data_by_id[stride_id] = (
                parts[header_index["num_helix_strand_turn"]],
                parts[header_index["num_helix"]],
                parts[header_index["num_strand"]],
                parts[header_index["num_helix_strand"]],
                parts[header_index["num_turn"]],
            )

    if not stride_data_by_id:
        raise ValueError(f"No data found in stride file: {file_path}")

    return stride_data_by_id


def transform_consensus(
    input_file,
    output_file,
    md5_file,
    stride_dir,
    stride_summary_suffix=DEFAULT_STRIDE_SUMMARY_SUFFIX,
    warn_missing_stride_id=False,
):
    headers = [
        "target_id",
        "MD5",
        "nres",
        "high",
        "med",
        "low",
        "high_dom",
        "med_dom",
        "low_dom",
    ]

    md5_lookup = read_md5_file(md5_file)

    # Read all stride summary files and combine their data
    all_stride_data_by_id = {}
    stride_files = [
        os.path.join(stride_dir, f)
        for f in os.listdir(stride_dir)
        if f.endswith(stride_summary_suffix)
    ]
    for stride_file in stride_files:
        _stride_data = read_stride_summary(stride_file, warn_missing_stride_id=warn_missing_stride_id)
        all_stride_data_by_id.update(_stride_data)

    stride_keys = [
        "num_helix_strand_turn",
        "num_helix",
        "num_strand",
        "num_helix_strand",
        "num_turn",
    ]

    column_names = [
        "uniprot_id",
        "md5_domain",
        "consensus_level",
        "chopping",
        "nres_domain",
        "num_segments",
    ] + stride_keys

    with open(input_file, newline="") as in_f, open(output_file, "w", newline="") as out_f:
        reader = csv.DictReader(in_f, fieldnames=headers, delimiter="\t")
        writer = csv.writer(out_f, delimiter="\t", lineterminator="\n")
        writer.writerow(column_names)

        for row in reader:
            uniprot_id = row["target_id"]
            domain_count = 1
            all_domains = []

            for level in ["high", "med"]:
                dom_str = row[f"{level}_dom"]
                if dom_str and dom_str.lower() != "na":
                    for domain in dom_str.split(","):
                        nres, num_segments, min_start = parse_domain(domain)
                        all_domains.append((min_start, domain, level, nres, num_segments))

            # Sort all domains by their lowest start residue.
            all_domains.sort(key=lambda d: d[0])

            for _, domain, level, nres, num_segments in all_domains:
                domain_id = f"{uniprot_id}_{domain_count:02d}"
                pdb_filename = f"{domain_id}.pdb"

                stride_values = all_stride_data_by_id.get(pdb_filename)
                if stride_values is None:
                    if warn_missing_stride_id:
                        print(f"WARNING: Stride summary data not found for ID '{pdb_filename}' (ignoring)", file=sys.stderr)
                        stride_values = ("NA", "NA", "NA", "NA", "NA")
                    else:
                        raise ValueError(f"Stride summary data not found for ID '{pdb_filename}'")

                md5 = md5_lookup.get(pdb_filename)
                if md5 is None:
                    raise KeyError(f"MD5 not found for domain '{pdb_filename}'")

                writer.writerow([
                    domain_id,
                    md5,
                    level,
                    domain,
                    nres,
                    num_segments,
                    *stride_values,
                ])
                domain_count += 1


# CLI use
if __name__ == "__main__":

    args = parser.parse_args()

    input_file = args.input_file
    output_file = args.output_file
    md5_file = args.md5_file
    stride_dir = args.stride_dir
    stride_summary_suffix = args.stride_summary_suffix

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file '{input_file}' does not exist.")

    if not os.path.exists(md5_file):
        raise FileNotFoundError(f"MD5 file '{md5_file}' does not exist.")

    if not os.path.exists(stride_dir):
        raise ValueError("Stride directory does not exist or is invalid.")

    transform_consensus(
        input_file,
        output_file,
        md5_file,
        stride_dir,
        stride_summary_suffix,
        warn_missing_stride_id=args.warn_missing_stride_id,
    )
