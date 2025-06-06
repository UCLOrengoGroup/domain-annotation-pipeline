import requests
import csv
import sys

# Manual list of UniProt IDs
accession = sys.argv[1]
output_file = sys.argv[2]

# Define header
header = [
    "accession",
    "proteome_id",
    "tax_common_name",
    "tax_scientific_name",
    "tax_lineage"
]

def fetch_uniprot_info(accession):
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

# Write one-row TSV
with open(output_file, "w", newline="") as tsvfile:
    writer = csv.DictWriter(tsvfile, fieldnames=header, delimiter="\t")
    writer.writeheader()
    writer.writerow(fetch_uniprot_info(accession))