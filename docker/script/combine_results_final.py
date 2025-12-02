# Merges the transformed consensus with plDDT and globularity outputs
# 2/6/25 Added a clause to merge on modified AF id and md5 columns and a warning if this fails.
# 5/6/25 Added clauses to merge taxonomic data
# 13/6/25 For BFVD: dropped all the construct_model_id and construct_af_domain_id functions.
# The pLDDT match is now done with md5.
# 20/8/25 added domain id to the join along with md5 to prevent duplication for identical domains.
# 1/12/25 added domain quality data merge

import pandas as pd
import argparse

QUALITY_COLNAMES=['PDB_ID', 'Chain_ID', 'Sequence_MD5', 'Dom_Domain_Count', 'DomQual']
QUALITY_DTYPES={'PDB_ID': str, 'Chain_ID': str, 'Sequence_MD5': str, 'Dom_Domain_Count': str, 'DomQual': float}
def run(transform_path, globularity_path, plddt_path, quality_path, foldseek_path, taxonomy_path, output_path):
    # Read input files
    transform_df = pd.read_csv(transform_path, sep='\t', dtype=str)
    glob_df = pd.read_csv(globularity_path, sep='\t', dtype=str)
    plddt_df = pd.read_csv(
        plddt_path, sep='\t', header=None,
        names=['plddt_id', 'avg_plddt', 'md5'],
        dtype={'plddt_id': str, 'md5': str}
    )
    quality_df = pd.read_csv(quality_path,
                             dtype=QUALITY_DTYPES,)

    quality_df['md5'] = quality_df['Sequence_MD5']
    quality_df['domqual'] = quality_df['DomQual']
    quality_df['dom_single_domain'] = quality_df['Dom_Domain_Count']
    quality_df['join_key'] = quality_df['PDB_ID'] + "_" + quality_df['md5']

    # Strip whitespace
    transform_df['md5_domain'] = transform_df['md5_domain'].str.strip()
    plddt_df['md5'] = plddt_df['md5'].str.strip()
    glob_df['md5'] = glob_df['md5'].str.strip()

    # --- Create consistent join keys: id + md5 ---
    # For transform, use uniprot_id + md5_domain
    transform_df['join_key'] = transform_df['uniprot_id'] + "_" + transform_df['md5_domain']

    # For globularity, use model_id + md5
    glob_df['join_key'] = glob_df['model_id'] + "_" + glob_df['md5']

    # For plddt, drop .pdb from id to match transform/glob
    plddt_df['plddt_id'] = plddt_df['plddt_id'].str.replace('.pdb', '', regex=False)
    plddt_df['join_key'] = plddt_df['plddt_id'] + "_" + plddt_df['md5']

    # --- Perform merges using id+md5 join key ---
    merged = transform_df.merge(
        glob_df.drop(columns=['chopping', 'md5']), on='join_key', how='left'
    )
    merged = merged.merge(
        plddt_df[['join_key', 'avg_plddt']], on='join_key', how='left'
    )
    merged = merged.merge(
        quality_df[['join_key', 'domqual', 'dom_single_domain']], on='join_key', how='left'
    )

    # Extract uniprot_id core for taxonomy merge
    merged['uniprot_core'] = merged['uniprot_id'].str.extract(r'([A-Z0-9]{6,})')
    
    # Merge foldseek data if provided
    if foldseek_path:
        fs_df = pd.read_csv(foldseek_path, sep='\t', dtype=str)
        fs_df = fs_df.rename(columns={
            'query_id': 'model_id', 
            'target_id': 'foldseek_match_id',
            'evalue': 'foldseek_evalue',
            'tmscore': 'foldseek_tmscore',
            'code': 'cath_label',
            'type': 'foldseek_match_type',
            'qcov': 'foldseek_query_cov',
            'tcov': 'foldseek_target_cov',
            }
            )
        # TODO: Change uniprot_id to model_id in (transformed consensus) everywhere else.
        merged = merged.merge(fs_df, left_on='uniprot_id', right_on='model_id', how='left')
    
    # Merge taxonomy if provided
    if taxonomy_path:
        tax_df = pd.read_csv(taxonomy_path, sep='\t', dtype=str)
        tax_df = tax_df.rename(columns={'accession': 'uniprot_core'})
        merged = merged.merge(tax_df, on='uniprot_core', how='left')

    # Drop internal join columns
    merged = merged.drop(columns=['uniprot_core', 'join_key'], errors='ignore')
    print("Columns in merged:", merged.columns.tolist())

    # Reorder columns to match expected output
    final_cols = [
        'uniprot_id', 'md5_domain', 'consensus_level', 'chopping', 'nres_domain',
        'num_segments', 'num_helix_strand_turn', 'num_helix', 'num_strand', 'num_helix_strand',
        'num_turn', 'packing_density', 'normed_radius_gyration', 'avg_plddt',
        'proteome_id', 'tax_common_name', 'tax_scientific_name', 'tax_lineage', 
        'domqual', 'dom_single_domain',
        'foldseek_match_id',
        'foldseek_evalue',
        'foldseek_tmscore',
        'cath_label',
        'foldseek_match_type',
        'foldseek_query_cov',
        'foldseek_target_cov'
    ]

    # Only keep columns that exist in the merged DataFrame
    final_cols = [col for col in final_cols if col in merged.columns]

    # Write to output
    merged.to_csv(output_path, sep='\t', index=False, columns=final_cols)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--transform', required=True)
    parser.add_argument('-g', '--globularity', required=True)
    parser.add_argument('-p', '--plddt', required=True)
    parser.add_argument('-q', '--quality', required=True)
    parser.add_argument('-f', '--foldseek', required=False)
    parser.add_argument('-x', '--taxonomy', required=False)
    parser.add_argument('-o', '--output', required=True)
    args = parser.parse_args()

    run(args.transform, args.globularity, args.plddt, args.quality, args.foldseek, args.taxonomy, args.output)
