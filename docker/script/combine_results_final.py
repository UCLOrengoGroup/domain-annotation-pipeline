# Merges the transformed consensus with plDDT and globularity outputs
# 2/6/25 Added a clause to merge on modified AF id and md5 columns and a warning if this fails.
# 5/6/25 Added clauses to merge taxonomic data

import pandas as pd
import argparse

def construct_model_id(ted_id, consensus_level):
    """Construct the model_id used in domain_globularity.tsv from ted_id and consensus_level."""
    base, ted_suffix = ted_id.rsplit('_TED', 1)  # Split into base and TEDXX
    return f"{base}_{consensus_level}_{int(ted_suffix)}"

def construct_af_domain_id(ted_id, chopping):
    """Construct the af_domain_id used in domain_plddt_and_lur.tsv from ted_id and chopping."""
    base = ted_id.rsplit('_TED', 1)[0]  # strip "_TED01"
    return f"{base}/{chopping}"

def run(transform_path, globularity_path, plddt_path, taxonomy_path, output_path):
    # Read transformed_consensus.tsv
    transform_df = pd.read_csv(transform_path, sep='\t', dtype=str)
    transform_df['model_id'] = transform_df.apply(
        lambda row: construct_model_id(row['ted_id'], row['consensus_level']), axis=1
    )
    print("Constructed model_id values for Glob match:")
    print(transform_df[['ted_id', 'consensus_level', 'model_id']])
    
    transform_df['af_domain_id'] = transform_df.apply(
        lambda row: construct_af_domain_id(row['ted_id'], row['chopping']), axis=1
    )
    print("Constructed af_domain_id values for plDDT match:")
    print(transform_df[['ted_id', 'chopping', 'af_domain_id']])
    # Read domain_globularity.tsv
    globularity_df = pd.read_csv(globularity_path, sep='\t', dtype=str)
    globularity_df = globularity_df[['model_id', 'md5', 'packing_density', 'normed_radius_gyration']]

    # Read domain_plddt_and_lur.tsv
    plddt_df = pd.read_csv(plddt_path, sep='\t', dtype=str)
    plddt_df = plddt_df[['af_domain_id', 'md5', 'avg_plddt']]

    # Merge using custom keys
    merged_df = (
        transform_df
        .merge(globularity_df, left_on=['model_id', 'md5_domain'], right_on=['model_id', 'md5'], how='left')
        .merge(plddt_df, left_on=['af_domain_id', 'md5_domain'], right_on=['af_domain_id', 'md5'], how='left')
    )
    # Add merge warnings for unmatched md5 columns
    import warnings
    if merged_df['packing_density'].isna().any():
        warnings.warn(
            f"{merged_df['packing_density'].isna().sum()} rows could not be matched with globularity data "
            f"(model_id + md5_domain)."
        )

    if merged_df['avg_plddt'].isna().any():
        warnings.warn(
            f"{merged_df['avg_plddt'].isna().sum()} rows could not be matched with plDDT data "
            f"(af_domain_id + md5_domain)."
        )
    
    # Merge taxonomy if provided
    if taxonomy_path:
        taxonomy_df = pd.read_csv(taxonomy_path, sep='\t', dtype=str)
        taxonomy_df = taxonomy_df.rename(columns={'accession': 'uniprot_id'})
        #merged_df['uniprot_id'] = merged_df['ted_id'].str.extract(r'(Q[A-Z0-9]{5,6})')
        merged_df['uniprot_id'] = merged_df['ted_id'].str.extract(r'([A-Z0-9]{6,})')
        merged_df = merged_df.merge(taxonomy_df, on='uniprot_id', how='left')

    # Final output column order
    output_cols = [
        'ted_id', 'md5_domain', 'consensus_level', 'chopping', 'nres_domain', 'num_segments',
        'num_helix_strand_turn', 'num_helix', 'num_strand', 'num_helix_strand', 'num_turn',
        'packing_density', 'normed_radius_gyration', 'avg_plddt', 'proteome_id', 'tax_common_name',
        'tax_scientific_name', 'tax_lineage'
    ]

    merged_df.to_csv(output_path, sep='\t', index=False, columns=output_cols)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--transform', required=True)
    parser.add_argument('-g', '--globularity', required=True)
    parser.add_argument('-p', '--plddt', required=True)
    parser.add_argument('-x', '--taxonomy', required=False)
    parser.add_argument('-o', '--output', required=True)
    args = parser.parse_args()

    run(args.transform, args.globularity, args.plddt, args.taxonomy, args.output)

