process run_stride {
    label 'sge_low'
    container 'domain-annotation-pipeline-cath-af-cli'
    publishDir "${params.results_dir}" , mode: 'copy', enabled: params.debug // only publish if run in debug mode

    input:
    tuple val(id), path(chopped_pdb_tar_file)
    path stride_summary_script

    output:
    tuple val(id), path("stride_batch_${id}.summary") //path('*.stride')

    script:
    """
    mkdir -p pdb
    tar -xzf ${chopped_pdb_tar_file} -C pdb
    cd pdb

    for f in *.pdb; do
        stride \$f > "../\${f%.pdb}.stride" 2> "../\${f%.pdb}.stride.err" || { 
        echo "STRIDE failed on \$f, see ../\${f%.pdb}.stride.err" 
        continue 
        }
    done
    cd ..
    
    python3 ${stride_summary_script} -o stride_batch_${id}.unsorted.summary -d . --suffix .stride

    head -n 1 stride_batch_${id}.unsorted.summary > stride_batch_${id}.summary
    tail -n +2 stride_batch_${id}.unsorted.summary | sort >> stride_batch_${id}.summary

    find . -maxdepth 1 -name '*.stride.err' -size 0 -delete
    rm -rf pdb
    rm -f *.stride
    rm -f stride_batch_${id}.unsorted.summary
    """
}
