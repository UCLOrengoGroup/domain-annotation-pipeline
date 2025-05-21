#!/bin/bash

stride_file="$1"

if [[ -f "$stride_file" ]]; then
  stride_ss=$(<"$stride_file")

  n_ss=$(grep -o "LOC" <<< "${stride_ss}" | wc -l)
  n_helix=$(grep -o "Helix" <<< "${stride_ss}" | wc -l)
  n_strand=$(grep -o "Strand" <<< "${stride_ss}" | wc -l)
  n_turn=$(grep -o "Turn" <<< "${stride_ss}" | wc -l)
else
  echo "File $stride_file not found!"
  n_ss=0
  n_helix=0
  n_strand=0
  n_turn=0
fi

n_helix_strand=$((n_helix + n_strand))

out_file="${stride_file}.summary" 
{
echo -e "num_helix_strand_turn:${n_ss} num_helix:${n_helix} num_strand:${n_strand} num_helix_strand:${n_helix_strand} num_turn:${n_turn}\n"
} > "$out_file"