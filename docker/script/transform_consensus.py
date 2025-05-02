# Takes the information in filtered_consensus.tsv and transforms it from model-level to doamin level.
# Input cols: AFDB_target_id', 'MD5', 'nres', 'high', 'med', 'low', 'high_dom', 'med_dom', 'low_dom'
# Output cols: AFDB_target_id', 'MD5', 'consensus_level', 'chopping', 'nres', 'num_segments'

import pandas as pd

def calculate_nres(domain):
    """Calculate total number of residues in a domain, including non-contiguous fragments."""
    fragments = domain.split('_')
    total = 0
    for frag in fragments:
        start, end = map(int, frag.split('-'))
        total += end - start + 1
    return total

def transform_consensus(input_file, output_file):
    # Define headers since input file has none
    headers = ['AFDB_target_id', 'MD5', 'nres', 'high', 'med', 'low', 'high_dom', 'med_dom', 'low_dom']
    df = pd.read_csv(input_file, sep='\t', names=headers)

    output_rows = []

    for idx, row in df.iterrows():
        pdb_id = row['AFDB_target_id']
        md5 = row['MD5']
        domain_count =1 #Start new count for each model domain

        for level in ['high', 'med']:
            dom_str = row[f'{level}_dom']
            if dom_str.lower() == 'na':
                continue  # Skip if no domains

            domains = dom_str.split(',')
            for domain in domains:
                new_id = f"{pdb_id}_TED{domain_count:02d}"
                nres = calculate_nres(domain)
                num_segments = domain.count('_') + 1
                output_rows.append([new_id, md5, level, domain, nres, num_segments])
                domain_count += 1 #Increment for each domain

    output_df = pd.DataFrame(output_rows, columns=['ted_id', 'md5_domain', 'consensus_level', 'chopping', 'nres_domain', 'num_segments'])
    output_df.to_csv(output_file, sep='\t', index=False)

# For command-line execution
if __name__ == '__main__':
    import sys
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    transform_consensus(input_file, output_file)
