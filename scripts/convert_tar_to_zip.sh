#!/bin/bash
#$ -N convert_tar_to_zip
#$ -cwd
#$ -l h_rt=02:00:00
#$ -l h_vmem=15G
#$ -pe smp 1
#$ -V

set -euo pipefail

echo "Starting job on $(hostname)"
echo "Running as user: $(whoami)"
echo "Working directory: $(pwd)"
echo "Date: $(date)"

INPUT_TAR=${1:-bfvd.tar.gz}

if [ ! -f "$INPUT_TAR" ]; then
  echo "Input file $INPUT_TAR does not exist."
  exit 1
fi

BASENAME=$(basename "$INPUT_TAR" .tar.gz)
TMPDIR="/scratch0/${USER}_${JOB_ID}_${BASENAME}"

echo "Creating temp directory: $TMPDIR"
mkdir -p "$TMPDIR"
cd "$TMPDIR"

echo "Copying archive to local scratch..."
cp "$SGE_O_WORKDIR/$INPUT_TAR" .

echo "Extracting PDB files..."
mkdir extracted
tar -xzf "$BASENAME.tar.gz" --wildcards --directory=extracted '*.pdb'

echo "Zipping PDB files from stdin..."
ZIP_NAME="${BASENAME}.zip"
cd extracted
find . -type f -name "*.pdb" -print0 | zip -q --names-stdin -0 "../$ZIP_NAME"

cd ..

echo "Copying zip archive back to $SGE_O_WORKDIR..."
cp "$ZIP_NAME" "$SGE_O_WORKDIR/"

echo "Cleaning up temporary files..."
rm -rf "$TMPDIR"

echo "Done at $(date)"