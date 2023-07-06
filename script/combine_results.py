import click
import pandas as pd

MERIZO_COLS = 'af_chain_id nres nres_dom nres_ndr ndom pIoU runtime result'.split()
UNIDOC_COLS = 'af_chain_id result'.split()
CHAINSAW_COLS = 'af_chain_id sequence_md5	nres ndom	result uncertainty'.split()
OUTPUT_COLS = {
    'af_chain_id': 'AlphaFold_ID',
    'result_chainsaw': 'Chainsaw',
    'result_merizo': 'Merizo',
    'result_unidoc': 'UniDoc',
}

@click.command()
@click.option('--merizo', '-m', 'merizo_file', type=click.File('rt'), 
              required=True, help='Merizo results file path (TSV)')
@click.option('--unidoc', '-u', 'unidoc_file', type=click.File('rt'), 
              required=True, help='UniDoc results file path (TSV)')
@click.option('--chainsaw', '-c', 'chainsaw_file', type=click.File('rt'),
              required=True, help='Chainsaw results file path (TSV)')
@click.option('--output', '-o', 'output_file', 
              required=True, help='Output result file path (TSV)')
def run(merizo_file, unidoc_file, chainsaw_file, output_file):
    merizo_df = pd.read_csv(merizo_file, sep='\t', header=None, names=MERIZO_COLS)
    merizo_df = normalise_df(merizo_df)
    merizo_df.rename(columns={'result': 'result_merizo'}, inplace=True)
    
    unidoc_df = pd.read_csv(unidoc_file, sep='\t', header=None, names=UNIDOC_COLS)
    unidoc_df = normalise_df(unidoc_df)
    unidoc_df.rename(columns={'result': 'result_unidoc'}, inplace=True)
    
    result_df = merizo_df.merge(unidoc_df, on='af_chain_id', how='outer')

    if chainsaw_file:
        chainsaw_df = pd.read_csv(chainsaw_file, sep='\t', header=None, names=CHAINSAW_COLS)
        chainsaw_df = normalise_df(chainsaw_df)
        chainsaw_df.rename(columns={'result': 'result_chainsaw'}, inplace=True)
        result_df = result_df.merge(chainsaw_df, on='af_chain_id', how='outer')
    else:
        result_df['result_chainsaw'] = [None] * result_df.shape[0]

    result_df = result_df[OUTPUT_COLS.keys()].rename(columns=OUTPUT_COLS)
    result_df.to_csv(output_file, sep='\t', index=False, header=True)

def normalise_df(df):
    # index by file stem (no suffix)
    df['af_chain_id'] = df['af_chain_id'].str.replace('.pdb', '').str.replace('.cif', '')
    return df


if __name__ == "__main__":
    run()