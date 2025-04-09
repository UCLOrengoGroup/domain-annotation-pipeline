"""
Standardise the output of merizo and unidoc results (adds corresponding md5s from chainsaw results)

usage:

    process_raw_results.py -c chainsaw_results.tsv -m merizo_results.tsv -o merizo_output_results.tsv
    process_raw_results.py -c chainsaw_results.tsv -u unidoc_results.tsv -o unidoc_output_results.tsv

"""

import pandas as pd
import argparse

#

VALID_TYPES = ["merizo", "unidoc"]

parser = argparse.ArgumentParser(
    description="Process merizo and unidoc files to standardise format."
)
parser.add_argument(
    "-c",
    "--chainsaw",
    type=str,
    required=True,
    help="Path to the chainsaw results file.",
)
parser.add_argument(
    "-m",
    "--merizo",
    type=str,
    required=False,
    help="Path to the merizo results file.",
)
parser.add_argument(
    "-u",
    "--unidoc",
    type=str,
    required=False,
    help="Path to the unidoc results file.",
)
parser.add_argument(
    "-o",
    "--output",
    type=str,
    required=True,
    help="Path to the output results file.",
)


def process_merizo(chainsaw_file, merizo_file, output_file):
    # Load chainsaw file
    chainsaw_df = pd.read_csv(
        chainsaw_file,
        sep="\t",
        header=None,
        usecols=[0, 1],
        names=["AF_chain_id", "sequence_md5"],
    )
    chainsaw_df["AF_chain_id"] = chainsaw_df["AF_chain_id"].astype(str)

    # Load merizo file
    merizo_df = pd.read_csv(
        merizo_file,
        sep="\t",
        header=None,
        usecols=[0, 1, 4, 5, 7],
        names=["AF_chain_id", "nres", "ndom", "PIoU", "result"],
    )
    merizo_df["AF_chain_id"] = merizo_df["AF_chain_id"].str.replace(
        ".pdb", "", regex=False
    )

    # Merge with chainsaw data
    merged_df = merizo_df.merge(chainsaw_df, on="AF_chain_id", how="left")
    final_df = merged_df[
        ["AF_chain_id", "sequence_md5", "nres", "ndom", "result", "PIoU"]
    ]

    # Save output
    final_df.to_csv(output_file, sep="\t", index=False, header=False)
    print(f"Processed merizo file saved to {output_file}")


def process_unidoc(chainsaw_file, unidoc_file, output_file):
    # Load chainsaw file
    chainsaw_df = pd.read_csv(
        chainsaw_file,
        sep="\t",
        header=None,
        usecols=[0, 1, 2],
        names=["AF_chain_id", "sequence_md5", "nres"],
    )
    chainsaw_df["AF_chain_id"] = chainsaw_df["AF_chain_id"].astype(str)

    # Load unidoc file
    unidoc_df = pd.read_csv(
        unidoc_file, sep="\t", header=None, names=["AF_chain_id", "result"]
    )

    # Count unique domains
    unidoc_df["ndom"] = unidoc_df["result"].apply(
        lambda x: (
            len(set([seg.split("_")[0] for seg in x.split(",")])) if pd.notna(x) else 0
        )
    )

    # Merge with chainsaw data
    merged_df = unidoc_df.merge(chainsaw_df, on="AF_chain_id", how="left")
    merged_df["PIoU"] = 1.00
    merged_df = merged_df[
        ["AF_chain_id", "sequence_md5", "nres", "ndom", "result", "PIoU"]
    ]

    # Save output
    merged_df.to_csv(output_file, sep="\t", index=False, header=False)
    print(f"Processed unidoc file saved to {output_file}")


def run():

    args = parser.parse_args()
    if args.merizo and args.unidoc:
        raise ValueError("Please provide either merizo or unidoc file, not both.")
    if args.merizo:
        process_merizo(args.chainsaw, args.merizo, args.output)
    if args.unidoc:
        process_unidoc(args.chainsaw, args.unidoc, args.output)


if __name__ == "__main__":
    run()
