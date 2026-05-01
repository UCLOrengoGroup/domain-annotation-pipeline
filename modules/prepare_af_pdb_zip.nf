/*
 * Convert a zip of AlphaFold BinaryCIF (.bcif) files into two zip files:
 * - one zip containing gzip-compressed CIF files (.cif.gz)
 * - one zip containing PDB (.pdb)
 *
 * The conversion can be limited by providing a list file of AFDB IDs (one per line).
 */

nextflow.enable.dsl = 2

process download_bcif_from_afdb {
    label 'sge_low'
    tag "$chunk_id"
    container 'domain-annotation-pipeline-script'
    publishDir "${params.results_dir}/prepared/chunks", mode: (params.publish_mode ?: 'copy')

    input:
    tuple val(chunk_id), path(afdb_ids_file)
  path download_script
    val base_url

    output:
    tuple(
    val(chunk_id),
    path("${chunk_id}.bcif_files.zip"),
    path("${chunk_id}.downloaded_ids.txt"),
    path("${chunk_id}.failed_ids.txt"),
    path("${chunk_id}.prep_summary.txt"),
    path("${chunk_id}.download_log.tsv")
    )

    script:
    """
    set -euo pipefail

    python3 "${download_script}" \
      --id-file "${afdb_ids_file}" \
      --base-url "${base_url}" \
      --out-bcif-zip bcif_files.zip

    mv bcif_files.zip "${chunk_id}.bcif_files.zip"
    mv downloaded_ids.txt "${chunk_id}.downloaded_ids.txt"
    mv failed_ids.txt "${chunk_id}.failed_ids.txt"
    mv prep_summary.txt "${chunk_id}.prep_summary.txt"
    mv download_log.tsv "${chunk_id}.download_log.tsv"
    """
}

process normalise_af_ids {
    label 'sge_low'
    container 'domain-annotation-pipeline-script'
    publishDir "${params.results_dir}/prepared", mode: (params.publish_mode ?: 'copy')

    input:
    path af_ids_file

    output:
    path 'af_ids.txt'

    script:
    """
    cat "${af_ids_file}" | tr -d '\\r' | sort -u > af_ids.txt
    """
}

process ids_from_bcif_zip {
    label 'sge_low'
    tag "$chunk_id"
    container 'domain-annotation-pipeline-script'
    publishDir "${params.results_dir}/prepared/chunks", mode: (params.publish_mode ?: 'copy')

    input:
    tuple val(chunk_id), path(bcif_zip_file)

    output:
    tuple val(chunk_id), path("${chunk_id}.af_ids.txt")

    script:
    """
    # Derive IDs from zip member names
    zipinfo -1 "${bcif_zip_file}" |
      tr -d '\\r' |
      sed 's#^.*/##' |
      sed 's#\\.bcif\$##' |
      sort -u > "${chunk_id}.af_ids.txt"
    """
}

process prepare_pdb_from_af_bcif {
    label 'sge_low'
    tag "$chunk_id"
    container 'domain-annotation-pipeline-script'
    publishDir "${params.results_dir}/prepared/chunks", mode: (params.publish_mode ?: 'copy')

    input:
    tuple val(chunk_id), path(bcif_zip), path(afdb_ids_file)
  path converter_script

    output:
    tuple val(chunk_id), path("${chunk_id}.cif_files.zip"), path("${chunk_id}.pdb_files.zip")

    script:
    """
    set -euo pipefail

    python3 "${converter_script}" \
      --bcif-zip "${bcif_zip}" \
      --list-file "${afdb_ids_file}" \
      --out-cif-zip cif_files.zip \
      --out-pdb-zip pdb_files.zip

    mv cif_files.zip "${chunk_id}.cif_files.zip"
    mv pdb_files.zip "${chunk_id}.pdb_files.zip"
    """
}
