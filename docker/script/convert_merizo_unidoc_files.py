import pandas as pd
import os

def process_merizo(chainsaw_file, merizo_file, output_file):
    # Load chainsaw file
    chainsaw_df = pd.read_csv(chainsaw_file, sep="\t", header=None, usecols=[0, 1], names=["AF_chain_id", "sequence_md5"])
    chainsaw_df["AF_chain_id"] = chainsaw_df["AF_chain_id"].astype(str)
    
    # Load merizo file
    merizo_df = pd.read_csv(merizo_file, sep="\t", header=None, usecols=[0, 1, 4, 5, 7], names=["AF_chain_id", "nres", "ndom", "PIoU", "result"])
    merizo_df["AF_chain_id"] = merizo_df["AF_chain_id"].str.replace(".pdb", "", regex=False)
    
    # Merge with chainsaw data
    merged_df = merizo_df.merge(chainsaw_df, on="AF_chain_id", how="left")
    final_df = merged_df[["AF_chain_id", "sequence_md5", "nres", "ndom", "result", "PIoU"]]
    
    # Save output
    final_df.to_csv(output_file, sep="\t", index=False, header=False)
    print(f"Processed merizo file saved to {output_file}")

def process_unidoc(chainsaw_file, unidoc_file, output_file):
    # Load chainsaw file
    chainsaw_df = pd.read_csv(chainsaw_file, sep="\t", header=None, usecols=[0, 1, 2], names=["AF_chain_id", "sequence_md5", "nres"])
    chainsaw_df["AF_chain_id"] = chainsaw_df["AF_chain_id"].astype(str)
    
    # Load unidoc file
    unidoc_df = pd.read_csv(unidoc_file, sep="\t", header=None, names=["AF_chain_id", "result"])
    
    # Count unique domains
    unidoc_df["ndom"] = unidoc_df["result"].apply(lambda x: len(set([seg.split("_")[0] for seg in x.split(",")])) if pd.notna(x) else 0)
    
    # Merge with chainsaw data
    merged_df = unidoc_df.merge(chainsaw_df, on="AF_chain_id", how="left")
    merged_df["PIoU"] = 1.00
    merged_df = merged_df[["AF_chain_id", "sequence_md5", "nres", "ndom", "result", "PIoU"]]
    
    # Save output
    merged_df.to_csv(output_file, sep="\t", index=False, header=False)
    print(f"Processed unidoc file saved to {output_file}")

if __name__ == "__main__":
    chainsaw_path = "chainsaw_results.tsv"   # "../domain_assignments.chainsaw.tsv"
    merizo_path =   "merizo_results.tsv"     # "../domain_assignments.merizo.tsv"
    unidoc_path =   "unidoc_results.tsv"     # "../domain_assignments.unidoc.tsv"
    merizo_output = "merizo_results_reformatted.tsv"   # "../domain_assignments.merizo_reformatted.tsv"
    unidoc_output = "unidoc_results_reformatted.tsv"   # "../domain_assignments.unidoc_reformatted.tsv"
    
    process_merizo(chainsaw_path, merizo_path, merizo_output)
    process_unidoc(chainsaw_path, unidoc_path, unidoc_output)
