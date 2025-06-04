# Takes the information in filtered_consensus.tsv and transforms it from model-level to doamin level.
# Input cols: AFDB_target_id', 'MD5', 'nres', 'high', 'med', 'low', 'high_dom', 'med_dom', 'low_dom'
# Output cols: ted_id', 'md5_domain', 'consensus_level', 'chopping', 'nres_domain', 'num_segments'
# Also parses STRIDE summary files (./results/stride), extracts the SSE fields and appends them to each row
# 23/5/25 - set MD5/md5_domain col to domain-level from md5_file to agree with globularity an plddt_and_lur programs.
# 27/5/25 - added error for non-existant md5 (line 72).
# Amended to read md5_file by named arguments rather than positional

import argparse
import pandas as pd
import os

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


def read_md5_file(md5_file):
    df = pd.read_csv(md5_file, sep="\t")
    md5_lookup = dict(zip(df["pdb_file"], df["md5"]))
    return md5_lookup


def calculate_nres(domain):
    fragments = domain.split("_")
    total = 0
    for frag in fragments:
        start, end = map(int, frag.split("-"))
        total += end - start + 1
    return total


def read_stride_summary(file_path):
    """
    Reads a STRIDE summary file (TSV) and returns a dictionary of dictionaries indexed by 'id'.

    Example of expected format:

        id      chain_id        num_helix_strand_turn   num_helix       num_strand      num_helix_strand        num_turn
        AF-Q6P9F5-F1-model_v4_med_1.pdb A       11      3       2       5       6

    """
    stride_data_by_id = dict()
    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError(f"Stride file '{file_path}' does not exist.")

    # Ensure all expected keys are present, even if they are not in the file
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
        header = f.readline().strip().split("\t")
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) != len(header):
                raise ValueError(f"Invalid format in stride file: {file_path}")
            stride_data = {}
            for key, value in zip(header, parts):
                if key not in expected_keys:
                    raise ValueError(
                        f"Unexpected key '{key}' in stride file: {file_path}"
                    )
                stride_data[key] = value

            stride_id = stride_data.get("id")
            stride_data_by_id[stride_id] = stride_data

    if not stride_data_by_id:
        raise ValueError(f"No data found in stride file: {file_path}")

    return stride_data_by_id


def transform_consensus(
    input_file,
    output_file,
    md5_file,
    stride_dir,
    stride_summary_suffix=DEFAULT_STRIDE_SUMMARY_SUFFIX,
):
    headers = [
        "AFDB_target_id",
        "MD5",
        "nres",
        "high",
        "med",
        "low",
        "high_dom",
        "med_dom",
        "low_dom",
    ]
    df = pd.read_csv(input_file, sep="\t", names=headers)

    md5_lookup = read_md5_file(md5_file)

    # Read all stride summary files and combine their data
    all_stride_data_by_id = {}
    stride_files = [
        os.path.join(stride_dir, f)
        for f in os.listdir(stride_dir)
        if f.endswith(stride_summary_suffix)
    ]
    for stride_file in stride_files:
        _stride_data = read_stride_summary(stride_file)
        for stride_id, data in _stride_data.items():
            all_stride_data_by_id[stride_id] = data

    output_rows = []
    stride_keys = [
        "num_helix_strand_turn",
        "num_helix",
        "num_strand",
        "num_helix_strand",
        "num_turn",
    ]

    for idx, row in df.iterrows():
        pdb_id = row["AFDB_target_id"]
        # md5 = row['MD5']
        domain_count = 1  # global TED number across both high and med domains

        for level in ["high", "med"]:
            dom_str = row[f"{level}_dom"]
            if isinstance(dom_str, str) and dom_str.lower() != "na":
                domains = dom_str.split(",")
                for domain in domains:
                    new_id = f"{pdb_id}_TED{domain_count:02d}"
                    nres = calculate_nres(domain)
                    num_segments = domain.count("_") + 1

                    if new_id not in all_stride_data_by_id:
                        raise KeyError(
                            f"Stride summary data not found for ID '{new_id}'"
                        )

                    stride_data = all_stride_data_by_id.get(new_id)

                    md5_id = f"{pdb_id}_{level}_{domain_count}.pdb"
                    if md5_id not in md5_lookup:
                        raise KeyError(f"MD5 not found for domain '{md5_id}'")
                    md5 = md5_lookup.get(md5_id)

                    row_data = [new_id, md5, level, domain, nres, num_segments]
                    for key in stride_keys:
                        row_data.append(stride_data.get(key, "NA"))

                    output_rows.append(row_data)
                    domain_count += 1

    column_names = [
        "ted_id",
        "md5_domain",
        "consensus_level",
        "chopping",
        "nres_domain",
        "num_segments",
    ] + stride_keys
    output_df = pd.DataFrame(output_rows, columns=column_names)
    output_df.to_csv(output_file, sep="\t", index=False)


# CLI use
if __name__ == "__main__":

    args = parser.parse_args()

    input_file = args.input_file
    output_file = args.output_file
    md5_file = args.md5_file
    stride_dir = args.stride_dir

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file '{input_file}' does not exist.")

    if not os.path.exists(md5_file):
        raise FileNotFoundError(f"MD5 file '{md5_file}' does not exist.")

    if not os.path.exists(stride_dir):
        raise ValueError("Stride directory does not exist or is invalid.")

    transform_consensus(input_file, output_file, md5_file, stride_dir)
