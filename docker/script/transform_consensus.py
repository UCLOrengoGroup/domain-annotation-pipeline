# Takes the information in filtered_consensus.tsv and transforms it from model-level to doamin level.
# Input cols: AFDB_target_id', 'MD5', 'nres', 'high', 'med', 'low', 'high_dom', 'med_dom', 'low_dom'
# Output cols: ted_id', 'md5_domain', 'consensus_level', 'chopping', 'nres_domain', 'num_segments'
# Also parses STRIDE summary files (./results/stride), extracts the SSE fields and appends them to each row
# 23/5/25 - set MD5/md5_domain col to domain-level from md5_file to agree with globularity an plddt_and_lur programs.
# 27/5/25 - added error for non-existant md5 (line 72).
# Amended to read md5_file by named arguments rather than positional

import pandas as pd
import os

def read_md5_file(md5_file):
    df = pd.read_csv(md5_file, sep='\t')
    md5_lookup = dict(zip(df['pdb_file'], df['md5']))
    return md5_lookup

def calculate_nres(domain):
    fragments = domain.split('_')
    total = 0
    for frag in fragments:
        start, end = map(int, frag.split('-'))
        total += end - start + 1
    return total

def read_stride_summary(file_path):
    stride_data = {}
    if not file_path or not os.path.exists(file_path):
        return {}
    with open(file_path) as f:
        line = f.readline().strip()
        stride_data = dict(item.split(':') for item in line.split())
    return stride_data

def transform_consensus(input_file, output_file, md5_file, stride_files):
    headers = ['AFDB_target_id', 'MD5', 'nres', 'high', 'med', 'low', 'high_dom', 'med_dom', 'low_dom']
    df = pd.read_csv(input_file, sep='\t', names=headers)
    
    md5_lookup = read_md5_file(md5_file)

# Build a lookup of stride summary files by their filename
    stride_lookup = {os.path.basename(f): f for f in stride_files}

    output_rows = []
    stride_keys = ['num_helix_strand_turn', 'num_helix', 'num_strand', 'num_helix_strand', 'num_turn']

    for idx, row in df.iterrows():
        pdb_id = row['AFDB_target_id']
        # md5 = row['MD5']
        domain_count = 1  # global TED number across both high and med domains

        for level in ['high', 'med']:
            dom_str = row[f'{level}_dom']
            if isinstance(dom_str, str) and dom_str.lower() != 'na':
                domains = dom_str.split(',')
                for domain in domains:
                    new_id = f"{pdb_id}_TED{domain_count:02d}"
                    nres = calculate_nres(domain)
                    num_segments = domain.count('_') + 1

                # Construct stride filename using the same global domain_count
                    stride_filename = f"{pdb_id}_{level}_{domain_count}.stride.summary"
                    stride_file = stride_lookup.get(stride_filename, None)
                    stride_data = read_stride_summary(stride_file)

                    md5_filename = f"{pdb_id}_{level}_{domain_count}.pdb"
                    if md5_filename not in md5_lookup:
                        raise KeyError(f"MD5 not found for domain '{md5_filename}'")
                    md5 = md5_lookup.get(md5_filename)
                    
                    row_data = [new_id, md5, level, domain, nres, num_segments]
                    for key in stride_keys:
                        row_data.append(stride_data.get(key, 'NA'))

                    output_rows.append(row_data)
                    domain_count += 1

    column_names = ['ted_id', 'md5_domain', 'consensus_level', 'chopping', 'nres_domain', 'num_segments'] + stride_keys
    output_df = pd.DataFrame(output_rows, columns=column_names)
    output_df.to_csv(output_file, sep='\t', index=False)

# CLI use
if __name__ == '__main__':
    import sys
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    md5_file = sys.argv[3]
    stride_files = sys.argv[4:]
    transform_consensus(input_file, output_file, md5_file, stride_files)

