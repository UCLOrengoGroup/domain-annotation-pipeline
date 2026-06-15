Generated with:

```bash
nextflow run workflows/prepare_af_pdb_zip.nf -profile docker \
    --af_ids_file af_ids_v6.txt \
    --prep_chunk_size 5 \
    --project_name bootstrap-sharded-fixtures
```