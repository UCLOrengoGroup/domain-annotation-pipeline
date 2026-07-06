# Domain Annotation Pipeline – Change Log

This file records major behavioural and configuration changes.

## 2026-07-06 (Chris Wyatt)
- **nf-core-style `bin/` refactor.** All pipeline scripts now live in a single `workflows/bin/` directory (moved from `docker/script/` and `foldseek/bin/`), are executable with `#!/usr/bin/env python3` shebangs, and are invoked by bare name. Scripts no longer need `params.*_script` path params or `path script` process inputs.
- The entry point is unchanged (`workflows/annotate.nf`), so `${projectDir}` = `workflows/` and Nextflow adds `workflows/bin` to the PATH of every task (host and container) automatically — no symlink required. Run command is unchanged: `nextflow run workflows/annotate.nf -profile debug,docker --input_zip_dir <dir> ...`.
- The `script` Docker image now builds from the repo root and installs `workflows/bin/*.py` onto the image PATH (`/usr/local/bin`); `docker-compose*.yml` and the build CI were updated accordingly.

## 2026-06-22 (Chris Wyatt)
- Updated for Nextflow 25.10+/26 (see README). Fixed `--chunk_size` which broke under v26 (now coerced to an integer before validation).
- Execution reports (timeline, report, trace, DAG) are now generated automatically into a timestamped `reports/` folder — no need to pass `-with-timeline`/`-with-report`/`-with-trace`.

## 2025-10-31 (Nick Edmunds)
- Added this changelog to track key updates.
- To run on the server must include a link to: -c /SAN/orengolab/bfvd/code/domain-annotation-pipeline/nextflow.config
- Order of profiles is now reversed:  -profile singularity,bfvd
- These parameters must be defined at runtime: chunk_size parameters, project_name, pdb_zip_file, uniprot_csv_file, min_chain_residues, max_entries and debug
