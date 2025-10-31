# Domain Annotation Pipeline – Change Log

This file records major behavioural and configuration changes.

## 2025-10-31 (Nick Edmunds)
- Added this changelog to track key updates.
- To run on the server must include a link to: -c /SAN/orengolab/bfvd/code/domain-annotation-pipeline/nextflow.config
- Order of profiles is now reversed:  -profile singularity,bfvd
- These parameters must be defined at runtime: chunk_size parameters, project_name, pdb_zip_file, uniprot_csv_file, min_chain_residues, max_entries and debug
