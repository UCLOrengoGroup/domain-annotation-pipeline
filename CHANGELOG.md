# Domain Annotation Pipeline – Change Log

This file records major behavioural and configuration changes.

## 2026-06-22 (Chris Wyatt) — TED segmentation concurrency
- Split `run_ted_segmentation` into three modules so Chainsaw runs concurrently with the Merizo→UniDoc chain (Chainsaw is independent; UniDoc inherits Merizo's chopping). New modules: `run_ted_merizo_unidoc` and `run_ted_chainsaw` (both GPU), and `run_ted_consensus` (CPU, `sge_low`) which joins the three choppings by `chunk_id` and computes consensus.
- Cuts this step's wall time to roughly `max(merizo+unidoc, chainsaw) + consensus`, at the cost of two GPU slots per chunk. Pipeline outputs are unchanged; the original `modules/run_ted_segmentation.nf` is retained but no longer used.

## 2026-06-22 (Chris Wyatt)
- Updated for Nextflow 25.10+/26 (see README). Fixed `--chunk_size` which broke under v26 (now coerced to an integer before validation).
- Execution reports (timeline, report, trace, DAG) are now generated automatically into a timestamped `reports/` folder — no need to pass `-with-timeline`/`-with-report`/`-with-trace`.

## 2025-10-31 (Nick Edmunds)
- Added this changelog to track key updates.
- To run on the server must include a link to: -c /SAN/orengolab/bfvd/code/domain-annotation-pipeline/nextflow.config
- Order of profiles is now reversed:  -profile singularity,bfvd
- These parameters must be defined at runtime: chunk_size parameters, project_name, pdb_zip_file, uniprot_csv_file, min_chain_residues, max_entries and debug
