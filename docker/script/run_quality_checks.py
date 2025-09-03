#!/usr/bin/env python3

"""
Script to process a directory of PDB files and generate a CSV file containing:
- PDB ID
- Chain ID  
- Sequence MD5
- Dom Domain Count (from dom tool)
- DomQual (from domqual tool)

Usage:
    python process_pdb_domains.py -d /path/to/pdb/directory -o output.csv --dom-path ./dom --domqual-path ../domqual/pytorch_foldclass_pred_dir.py
"""

import os
import re
import csv
import hashlib
import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from Bio.SeqUtils import seq1
from Bio.PDB.PDBParser import PDBParser
from Bio.PDB import Polypeptide

def extract_pdb_chain_info(pdb_file: str) -> List[Tuple[str, str, str]]:
    """
    Extract PDB ID, chain ID, and sequence MD5 from a PDB file.
    
    Args:
        pdb_file (str): Path to PDB file
        
    Returns:
        List of tuples containing (pdb_id, chain_id, sequence_md5)
    """
    results = []
    parser = PDBParser(QUIET=True)
    
    try:
        # Extract PDB ID from filename (e.g., A0A023ZWU6_01.pdb -> A0A023ZWU6_01)
        pdb_id = Path(pdb_file).stem
        
        structure = parser.get_structure('structure', pdb_file)
        
        for model in structure:
            for chain in model:
                chain_id = chain.get_id()
                
                # Extract sequence from chain
                sequence = ""
                for residue in chain:
                    if Polypeptide.is_aa(residue.get_resname(), standard=True):
                        sequence += seq1(residue.get_resname())
                
                # Calculate MD5 hash of sequence
                if sequence:
                    sequence_md5 = hashlib.md5(sequence.encode()).hexdigest()
                    results.append((pdb_id, chain_id, sequence_md5))
                    
    except Exception as e:
        print(f"Error processing {pdb_file}: {e}", file=sys.stderr)
        
    return results


def run_dom_analysis(pdb_file: str, dom_path: str) -> int:
    """
    Run dom tool on PDB file and extract domain count.
    
    Args:
        pdb_file (str): Path to PDB file
        dom_path (str): Path to dom executable
        
    Returns:
        int: Number of domains predicted
    """
    try:
        # Run dom command
        result = subprocess.run(
            [dom_path, pdb_file],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"Dom analysis failed for {pdb_file}: {result.stderr}", file=sys.stderr)
            return 0
            
        # Parse output to extract domain count
        output = result.stdout
        
        # Look for "assign X domain" lines
        domain_assignments = re.findall(r'assign\s+(\d+)\s+domain', output)
        
        if domain_assignments:
            # Get the final domain count (last assignment)
            return int(domain_assignments[-1])
        
        return 0
        
    except subprocess.TimeoutExpired:
        print(f"Dom analysis timed out for {pdb_file}", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"Error running dom analysis on {pdb_file}: {e}", file=sys.stderr)
        return 0


def run_domqual_analysis(pdb_file: str, domqual_script: str) -> Dict[str, float]:
    """
    Run domqual analysis on directory and extract quality scores.
    
    Args:
        pdb_file (str): PDB file
        domqual_script (str): Path to domqual Python script
        
    Returns:
        Dict mapping PDB filenames to quality scores
    """
    quality_scores = {}
    
    try:
        # Run domqual script on entire directory
        result = subprocess.run(
            ['python3', domqual_script, pdb_file],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            print(f"DomQual analysis failed: {result.stderr}", file=sys.stderr)
            return quality_scores
            
        # Parse output to extract quality scores
        output = result.stdout
        
        # Look for lines like "example_pdbs/A0A023GZ41_01.pdb 0.788040816783905"
        for line in output.split('\n'):
            if '.pdb' in line and not line.startswith('Torch'):
                parts = line.strip().split()
                if len(parts) >= 2:
                    pdb_path = parts[0]
                    try:
                        score = float(parts[1])
                        # Extract just the filename
                        pdb_filename = Path(pdb_path).name
                        quality_scores[pdb_filename] = score
                    except (ValueError, IndexError):
                        continue
                        
    except subprocess.TimeoutExpired:
        print("DomQual analysis timed out", file=sys.stderr)
    except Exception as e:
        print(f"Error running domqual analysis: {e}", file=sys.stderr)
        
    return quality_scores


def process_pdb_directory(
    pdb_directory: str,
    output_file: str,
    dom_path: str,
    domqual_script: str
) -> None:
    """
    Process all PDB files in directory and generate CSV output.
    
    Args:
        pdb_directory (str): Directory containing PDB files
        output_file (str): Output CSV file path
        dom_path (str): Path to dom executable
        domqual_script (str): Path to domqual Python script
    """
    
    # Get list of PDB files
    pdb_files = list(Path(pdb_directory).glob("*.pdb"))
    
    if not pdb_files:
        print(f"No PDB files found in {pdb_directory}")
        return
        
    print(f"Found {len(pdb_files)} PDB files")
    
    
    # Process each PDB file
    results = []
    
    for i, pdb_file in enumerate(pdb_files, 1):
        print(f"Processing {pdb_file.name} ({i}/{len(pdb_files)})")
        
        # Extract PDB and chain information
        pdb_chain_info = extract_pdb_chain_info(str(pdb_file))
        
        if not pdb_chain_info:
            print(f"Warning: No valid chains found in {pdb_file.name}")
            continue
            
        # Run dom analysis
        domain_count = run_dom_analysis(str(pdb_file), dom_path)

        # Run domqual analysis on entire directory first
        print("Running DomQual analysis...")
        quality_scores = run_domqual_analysis(str(pdb_file), domqual_script)

        # Get quality score
        quality_score = quality_scores.get(pdb_file.name, 0.0)
        
        # Add results for each chain
        for pdb_id, chain_id, sequence_md5 in pdb_chain_info:
            results.append({
                'PDB_ID': pdb_id,
                'Chain_ID': chain_id,
                'Sequence_MD5': sequence_md5,
                'Dom_Domain_Count': domain_count,
                'DomQual': quality_score
            })
    
    # Write results to CSV
    print(f"Writing results to {output_file}")
    
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['PDB_ID', 'Chain_ID', 'Sequence_MD5', 'Dom_Domain_Count', 'DomQual']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Successfully processed {len(results)} entries")


def main():
    """Main function to parse arguments and run processing."""
    parser = argparse.ArgumentParser(
        description="Process PDB files to extract domain information and quality scores",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -d example_pdbs/ -o results.csv --dom-path ./dom --domqual-path ../domqual/pytorch_foldclass_pred.py
  %(prog)s -d /data/structures/ -o domain_analysis.csv --dom-path /usr/local/bin/dom --domqual-path ./domqual.py
        """
    )
    
    parser.add_argument(
        '-d', '--directory',
        required=True,
        help='Directory containing PDB files'
    )
    
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output CSV file path'
    )
    
    parser.add_argument(
        '--dom-path',
        required=True,
        help='Path to dom executable'
    )
    
    parser.add_argument(
        '--domqual-path',
        required=True,
        help='Path to domqual Python script'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist", file=sys.stderr)
        sys.exit(1)
        
    if not os.path.exists(args.dom_path):
        print(f"Error: Dom executable '{args.dom_path}' does not exist", file=sys.stderr)
        sys.exit(1)
        
    if not os.path.exists(args.domqual_path):
        print(f"Error: DomQual script '{args.domqual_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    try:
        process_pdb_directory(
            args.directory,
            args.output,
            args.dom_path,
            args.domqual_path
        )
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

