#!/usr/bin/env python3

"""
Script to process a directory of PDB files and generate a CSV file containing:
- PDB ID
- Chain ID  
- Sequence MD5
- Dom Domain Count (from dom tool)
- DomQual (from domqual tool)

Usage:
    python run_quality_checks.py -d /path/to/pdb/directory -o output.csv --dom-path ./dom --domqual-path ../domqual/pytorch_foldclass_pred_dir.py
"""

import os
import re
import csv
import hashlib
import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Iterator
from Bio.SeqUtils import seq1
from Bio.PDB.PDBParser import PDBParser
from Bio.PDB import Polypeptide


def get_pdb_files_efficiently(
    pdb_directory: str
) -> Iterator[Path]:
    """
    Efficiently iterate through PDB files in a large directory.
    
    Args:
        pdb_directory (str): Directory containing PDB files
        
    Yields:
        Path: PDB file paths
        
    Note:
        Uses os.scandir() for better performance with large directories.
    """
    pdb_dir_path = Path(pdb_directory)
    
    try:
        # Use os.scandir() for better performance than glob() on large directories
        with os.scandir(pdb_directory) as entries:
            for entry in entries:
                # Check if it's a PDB file
                if entry.is_file() and entry.name.endswith('.pdb'):
                    yield pdb_dir_path / entry.name
                        
    except OSError as e:
        raise OSError(f"Error scanning directory {pdb_directory}: {e}")


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


def run_domqual_analysis(pdb_dir: str, domqual_script: str) -> Dict[str, float]:
    """
    Run domqual analysis on directory and extract quality scores.
    
    Args:
        pdb_dir (str): PDB directory
        domqual_script (str): Path to domqual Python script
        
    Returns:
        Dict mapping PDB filenames to quality scores
    """
    quality_scores = {}
    
    try:
        # Run domqual script on entire directory
        result = subprocess.run(
            ['python3', domqual_script, pdb_dir],
            capture_output=True,
            text=True,
            timeout=600  # Increased timeout for large directories
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
    domqual_script: str,
    batch_size: int = 1000
) -> None:
    """
    Process PDB files in directory and generate CSV output.
    
    Args:
        pdb_directory (str): Directory containing PDB files
        output_file (str): Output CSV file path
        dom_path (str): Path to dom executable
        domqual_script (str): Path to domqual Python script
        batch_size (int): Number of files to process before writing intermediate results
    """
        
    # Get iterator for PDB files (much more memory efficient for large directories)
    pdb_files_iter = get_pdb_files_efficiently(pdb_directory)
    
    # Run domqual analysis on entire directory first (if needed)
    print("Running DomQual analysis...")
    quality_scores = run_domqual_analysis(pdb_directory, domqual_script)
    
    # Process files in batches to manage memory and provide progress updates
    results = []
    processed_count = 0
    found_files = set()
    
    # Open output file for writing
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['PDB_ID', 'Chain_ID', 'Sequence_MD5', 'Dom_Domain_Count', 'DomQual']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for pdb_file in pdb_files_iter:
            processed_count += 1
            found_files.add(pdb_file.name)
            
            if processed_count % 100 == 0:
                print(f"Processed {processed_count} files...")
            
            # Extract PDB and chain information
            pdb_chain_info = extract_pdb_chain_info(str(pdb_file))
            
            if not pdb_chain_info:
                print(f"Warning: No valid chains found in {pdb_file.name}")
                continue
                
            # Run dom analysis
            domain_count = run_dom_analysis(str(pdb_file), dom_path)
            
            # Get quality score
            quality_score = quality_scores.get(pdb_file.name, 0.0)
            
            # Add results for each chain
            batch_results = []
            for pdb_id, chain_id, sequence_md5 in pdb_chain_info:
                batch_results.append({
                    'PDB_ID': pdb_id,
                    'Chain_ID': chain_id,
                    'Sequence_MD5': sequence_md5,
                    'Dom_Domain_Count': domain_count,
                    'DomQual': quality_score
                })
            
            # Write batch results immediately to save memory
            writer.writerows(batch_results)
            results.extend(batch_results)  # Keep for final count
            
            # Flush periodically for large datasets
            if processed_count % batch_size == 0:
                csvfile.flush()
    
    # Report missing files if we had a target list
    if target_filenames:
        missing_files = target_filenames - found_files
        if missing_files:
            print(f"\nWarning: {len(missing_files)} specified files not found:")
            for filename in sorted(list(missing_files)[:10]):  # Show first 10
                print(f"  - {filename}")
            if len(missing_files) > 10:
                print(f"  ... and {len(missing_files) - 10} more")
    
    print("\nProcessing complete!")
    print(f"Files processed: {processed_count}")
    print(f"Total entries written: {len(results)}")
    print(f"Results written to: {output_file}")


def main():
    """Main function to parse arguments and run processing."""
    parser = argparse.ArgumentParser(
        description="Process PDB files to extract domain information and quality scores",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all PDB files (streaming for large directories)
  %(prog)s -d /large/pdb/directory/ -o results.csv --dom-path ./dom --domqual-path ./domqual.py

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
        
    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='Number of files to process before flushing output (default: 1000)'
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
            args.domqual_path,
            args.batch_size
        )
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

