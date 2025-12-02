# Merges the transformed consensus with plDDT and globularity outputs
# 2/6/25 Added a clause to merge on modified AF id and md5 columns and a warning if this fails.
# 5/6/25 Added clauses to merge taxonomic data
# 13/6/25 For BFVD: dropped all the construct_model_id and construct_af_domain_id functions.
# The pLDDT match is now done with md5.
# 20/8/25 added domain id to the join along with md5 to prevent duplication for identical domains.

import pandas as pd
import argparse
import numpy as np

def run(transform_path, globularity_path, plddt_path, foldseek_path, taxonomy_path, output_path):
    # Read input files
    transform_df = pd.read_csv(transform_path, sep='\t', dtype=str)
    glob_df = pd.read_csv(globularity_path, sep='\t', dtype=str)
    plddt_df = pd.read_csv(
        plddt_path, sep='\t', header=None,
        names=['plddt_id', 'avg_plddt', 'md5'],
        dtype={'plddt_id': str, 'md5': str}
    )

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

    # Add calculation of Q-score here
    if 'foldseek_evalue' in merged.columns:
        # Convert necessary fields back to numeric datatypes
        merged['avg_plddt'] = pd.to_numeric(merged['avg_plddt']) #, errors="coerce")
        merged['foldseek_query_cov'] = pd.to_numeric(merged['foldseek_query_cov']) #, errors="coerce")
        merged['foldseek_target_cov'] = pd.to_numeric(merged['foldseek_target_cov']) #, errors="coerce")
        merged['foldseek_evalue'] = pd.to_numeric(merged['foldseek_evalue']) #, errors="coerce")
        merged['packing_density'] = pd.to_numeric(merged['packing_density'])
        merged['normed_radius_gyration'] = pd.to_numeric(merged['normed_radius_gyration'])
        # re-scale plddt to 0-1
        plddt = merged['avg_plddt']/100
        # calculate consensus marker
        consensus = np.where((merged['consensus_level']== "high"), 1.0, 0.5)
        # calculate globularity marker
        globularity = np.where((merged['packing_density'] >= 10.333) & (merged['normed_radius_gyration'] < 0.356), 1.0, 0.0)
        # calculate an EV value
        factor = np.log(0.5) / 0.01
        evalue = merged['foldseek_evalue']
        ev_raw = np.exp(factor * evalue.fillna(0))
        ev = np.where(evalue.notna(), np.maximum(ev_raw, 0.5), 0.5)
        # calculate the minimum qcov, tcov value
        min_cov = np.minimum(merged['foldseek_query_cov'].fillna(0), merged['foldseek_target_cov'].fillna(0))
        # calculate the final: Q-score
        merged['Q_score'] = round(100 * (
            4 * min_cov
            + consensus
            + globularity
            + plddt
            + ev
        ) / 8.0, 2)

    # Reorder columns to match expected output
    final_cols = [
        'uniprot_id', 'md5_domain', 'consensus_level', 'chopping', 'nres_domain',
        'num_segments', 'num_helix_strand_turn', 'num_helix', 'num_strand', 'num_helix_strand',
        'num_turn', 'packing_density', 'normed_radius_gyration', 'avg_plddt',
        'proteome_id', 'tax_common_name', 'tax_scientific_name', 'tax_lineage', 
        'foldseek_match_id',
        'foldseek_evalue',
        'foldseek_tmscore',
        'cath_label',
        'foldseek_match_type',
        'foldseek_query_cov',
        'foldseek_target_cov',
        'Q_score'
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
    parser.add_argument('-f', '--foldseek', required=False)
    parser.add_argument('-x', '--taxonomy', required=False)
    parser.add_argument('-o', '--output', required=True)
    args = parser.parse_args()

    run(args.transform, args.globularity, args.plddt, args.foldseek, args.taxonomy, args.output)
