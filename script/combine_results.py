import click
import pandas as pd

MERIZO_COLS = 'af_chain_id nres nres_dom nres_ndr ndom pIoU runtime result'.split()
UNIDOC_COLS = 'af_chain_id result'.split()
CHAINSAW_COLS = 'af_chain_id result'.split()
OUTPUT_COLS = {
    'af_chain_id': 'model_id',
    'result_chainsaw': 'Chainsaw',
    'result_merizo': 'Merizo',
    'result_unidoc': 'UniDoc',
}

@click.command()
@click.option('--merizo', '-m', 'merizo_file', type=click.File('rt'), 
              required=True, help='Merizo results file path (TSV)')
@click.option('--unidoc', '-u', 'unidoc_file', type=click.File('rt'), 
              required=True, help='UniDoc results file path (TSV)')
@click.option('--chainsaw', '-c', 'chainsaw_file', 
              required=False, help='Chainsaw results file path (TSV)')
@click.option('--output', '-o', 'output_file', 
              required=True, help='Output result file path (TSV)')
def run(merizo_file, unidoc_file, chainsaw_file, output_file):
    merizo_df = pd.read_csv(merizo_file, sep='\t', header=None, names=MERIZO_COLS)
    merizo_df = normalise_df(merizo_df)
    
    unidoc_df = pd.read_csv(unidoc_file, sep='\t', header=None, names=UNIDOC_COLS)
    unidoc_df = normalise_df(unidoc_df)

    result_df = merizo_df.join(unidoc_df, how='outer', lsuffix='_merizo', rsuffix='_unidoc')

    chainsaw_df = None
    if chainsaw_file:
        chainsaw_df = pd.read_csv(chainsaw_file, sep='\t', header=None, names=CHAINSAW_COLS)
        chainsaw_df = normalise_df(chainsaw_df)
        result_df = result_df.join(chainsaw_df, how='outer', rsuffix='_chainsaw')
    else:
        result_df['result_chainsaw'] = [None] * result_df.shape[0]

    result_df['af_chain_id'] = result_df.index
    # print(result_df.head())

    result_df = result_df[OUTPUT_COLS.keys()].rename(OUTPUT_COLS)
    result_df.to_csv(output_file, sep='\t', index=False, header=True)


def normalise_df(df):
    df['index'] = df['af_chain_id'].str.replace('.pdb', '')

    df.set_index('index', inplace=True)
    return df


if __name__ == "__main__":
    run()