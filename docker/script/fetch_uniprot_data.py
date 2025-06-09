import requests
import csv
import argparse

def fetch_uniprot_info(accession):
    """Fetch UniProt taxonomy and proteome metadata for a given accession."""
    url = f"https://rest.uniprot.org/uniprotkb/search?query=accession:{accession}&fields=xref_proteomes,organism_name&format=json"
    response = requests.get(url)
    data = response.json()
    
    try:
        result = data['results'][0]
        proteome_info = next(
            (ref for ref in result['uniProtKBCrossReferences'] if ref['database'] == 'Proteomes'),
            {}
        )
        proteome_id = proteome_info.get('id', '')
        tax_id = result['organism']['taxonId']
        lineage = result['organism']['lineage']
        return {
            "accession": accession,
            "proteome_id": f"proteome-tax_id-{tax_id}-0_v4",
            "tax_common_name": result['organism'].get('commonName', ''),
            "tax_scientific_name": result['organism'].get('scientificName', ''),
            "tax_lineage": ';'.join(lineage)
        }
    except (IndexError, KeyError) as e:
        print(f"Failed to parse data for {accession}: {e}")
        return {
            "accession": accession,
            "proteome_id": '',
            "tax_common_name": '',
            "tax_scientific_name": '',
            "tax_lineage": ''
        }

def run(accession, output_file):
    """Fetch metadata for UniProt ID and write a one-row TSV file."""
    header = [
        "accession",
        "proteome_id",
        "tax_common_name",
        "tax_scientific_name",
        "tax_lineage"
    ]
    
    data = fetch_uniprot_info(accession)
    with open(output_file, "w", newline="") as tsvfile:
        writer = csv.DictWriter(tsvfile, fieldnames=header, delimiter="\t")
        writer.writeheader()
        writer.writerow(data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch taxonomy and proteome info from UniProt")
    parser.add_argument('-a', '--accession', required=True, help='UniProt accession (e.g. Q9Y2T1)')
    parser.add_argument('-o', '--output', required=True, help='Output TSV file path')
    args = parser.parse_args()

    run(args.accession, args.output)