#!/usr/bin/env python3
# Vendored from https://github.com/sillitoe/ted-tools (v0.1.2),
# ted_consensus_1.0/scripts/. Previously baked into the ted-tools container
# image; now maintained in-repo here and NOT auto-updated from upstream.

"""
Script to process a directory of PDB files and generate a CSV file containing:
- PDB ID
- Chain ID  
- Sequence MD5
- Dom Domain Count (from dom tool)
- DomQual (from domqual tool)

Usage:
    python run_quality_checks.py -d /path/to/pdb/directory -o output.csv --dom-path ../other-tools/dom_v2/domain --domqual-path ../other-tools/domqual/pytorch_foldclass_pred_dir.py
"""

import os
import re
import csv
import hashlib
import argparse
import subprocess
import sys
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Iterator, Optional
from Bio.SeqUtils import seq1
from Bio.PDB.PDBParser import PDBParser
from Bio.PDB import Polypeptide


DOM_RESULT_MATCH = re.compile(r'(?P<dom_count_normal>[0-9]+)\s+on\s+(?P<dom_count_smoothed>[0-9]+)\s+domains,\s+(?P<dom_pct_agree>[0-9.]+)\s+pct.\s+agree')
DOM_MIN_AGREEMENT = 80  # Minimum percentage agreement to consider dom result valid

TOOLS_DIR = Path(__file__).parent / '../../other-tools'
DEFAULT_DOM_PATH = TOOLS_DIR / 'dom_v2/domain'
DEFAULT_DOMQUAL_PATH = TOOLS_DIR / 'domqual/pytorch_foldclass_pred_dir.py'


def format_sigfigs(value: float, sigfigs: int = 5) -> str:
    """Format a float to a given number of significant figures for output."""
    if value == 0 or value == 0.0:
        return "0"
    return f"{value:.{sigfigs}g}"



def get_pdb_files_from_directory(pdb_directory: str) -> Iterator[Path]:
    pdb_dir_path = Path(pdb_directory)
    try:
        with os.scandir(pdb_directory) as entries:
            for entry in entries:
                if entry.is_file() and entry.name.endswith('.pdb'):
                    yield pdb_dir_path / entry.name
    except OSError as e:
        raise OSError(f"Error scanning directory {pdb_directory}: {e}")

def get_pdb_files_from_zip(zip_path: str, file_list: Optional[str] = None) -> Iterator[Path]:
    """
    Yields Path-like objects to temp files extracted from the zip.
    If file_list is provided, only those files are extracted; otherwise, all .pdb files in the zip.
    """
    with zipfile.ZipFile(zip_path, 'r') as z:
        if file_list:
            with open(file_list) as f:
                wanted = set(line.strip() for line in f if line.strip())
            members = [m for m in z.namelist() if m in wanted]
        else:
            members = [m for m in z.namelist() if m.endswith('.pdb')]
        for member in members:
            with z.open(member) as src, tempfile.NamedTemporaryFile('wb', delete=False, suffix='.pdb') as tmp:
                tmp.write(src.read())
                tmp.flush()
                yield Path(tmp.name)


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
        raise RuntimeError(f"Error processing {pdb_file}: {e}", file=sys.stderr)
        
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
        # If the process was terminated by a signal, returncode will be negative
        if result.returncode < 0:
            sig = -result.returncode
            print(f"Dom crashed for {pdb_file}: terminated by signal {sig}", file=sys.stderr)
            if result.stdout:
                print(f"Dom stdout:\n{result.stdout}", file=sys.stderr)
            if result.stderr:
                print(f"Dom stderr:\n{result.stderr}", file=sys.stderr)
            return 0
        elif result.returncode > 0:
            # Non-zero exit (but not signal) - show stderr for debugging
            print(f"Dom analysis failed for {pdb_file}: exit {result.returncode}", file=sys.stderr)
            if result.stderr:
                print(f"Dom stderr:\n{result.stderr}", file=sys.stderr)
            if result.stdout:
                print(f"Dom stdout:\n{result.stdout}", file=sys.stderr)
            return 0
            
        # Parse output to extract domain count
        output = result.stdout

        # Look for final assignment output
        # 1 on 1 domains, 100 pct. agree
        match = DOM_RESULT_MATCH.search(output)
        if match:
            dom_count_normal = int(match.group('dom_count_normal'))
            dom_count_smoothed = int(match.group('dom_count_smoothed'))
            dom_pct_agree = float(match.group('dom_pct_agree'))

            quality_check_result = True if dom_count_normal == 1 and dom_count_smoothed == 1 and dom_pct_agree >= DOM_MIN_AGREEMENT else False
            print(f"{pdb_file} Dom analysis: normal={dom_count_normal}, smoothed={dom_count_smoothed}, pct_agree={dom_pct_agree}, quality_check={quality_check_result}")
            return quality_check_result
        else:
            msg = f"Could not parse dom output for {pdb_file} (output: {output})"
            raise ValueError(msg)
        
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
            # timeout=60 * 60 * 2  # Increased timeout for large directories
        )
        
        if result.returncode != 0:
            # print(f"DomQual analysis failed: {result.stderr}", file=sys.stderr)
            raise RuntimeError(f"DomQual analysis failed with exit code {result.returncode}, stderr: {result.stderr}")
            
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
                        print(f"DomQual score for {pdb_filename}: {score}")
                        quality_scores[pdb_filename] = score
                    except (ValueError, IndexError):
                        continue
                        
    except subprocess.TimeoutExpired:
        print("DomQual analysis timed out", file=sys.stderr)
    except Exception as e:
        print(f"Error running domqual analysis: {e}", file=sys.stderr)
        
    return quality_scores



def process_pdb_inputs(
    pdb_directory: Optional[str],
    pdb_zip: Optional[str],
    pdb_zip_list: Optional[str],
    output_file: str,
    dom_path: str,
    domqual_script: str,
    batch_size: int = 1000
) -> None:
    """
    Process PDB files from a directory or zip and generate CSV output.
    """
    temp_dir = None
    if pdb_directory:
        pdb_files_iter = get_pdb_files_from_directory(pdb_directory)
        domqual_input = pdb_directory
    elif pdb_zip:
        # Extract selected members (or all .pdb) into a temporary directory so
        # original basenames are preserved and domqual can be run on that folder.
        temp_dir = tempfile.TemporaryDirectory()
        with zipfile.ZipFile(pdb_zip, 'r') as z:
            all_members = z.namelist()
            if pdb_zip_list:
                with open(pdb_zip_list) as f:
                    wanted = [line.strip() for line in f if line.strip()]

                # Build a map from basename -> members (to handle nested paths inside zip)
                basename_map = {}
                for m in all_members:
                    base = Path(m).name
                    basename_map.setdefault(base, []).append(m)

                members = []
                missing = []
                for w in wanted:
                    if w in all_members:
                        members.append(w)
                    elif w in basename_map:
                        # Prefer the first match if there are multiple entries with same basename
                        members.append(basename_map[w][0])
                        if len(basename_map[w]) > 1:
                            print(f"Warning: multiple entries in zip match '{w}'; using '{basename_map[w][0]}'", file=sys.stderr)
                    else:
                        missing.append(w)

                if missing:
                    print(f"Warning: the following entries from --zip-list were not found in the zip: {', '.join(missing)}", file=sys.stderr)
            else:
                members = [m for m in all_members if m.endswith('.pdb')]
            for member in members:
                # ensure directories exist
                target_path = Path(temp_dir.name) / member
                target_path.parent.mkdir(parents=True, exist_ok=True)
                z.extract(member, temp_dir.name)
        # Iterate over extracted files (preserves original filenames)
        def _iter_extracted():
            for member in members:
                yield Path(temp_dir.name) / member
        pdb_files_iter = _iter_extracted()
        domqual_input = temp_dir.name
    else:
        raise ValueError("Must specify either a PDB directory or a zip file.")

    print("Running DomQual analysis...")
    quality_scores = run_domqual_analysis(domqual_input, domqual_script)

    results = []
    processed_count = 0
    found_files = set()

    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['PDB_ID', 'Chain_ID', 'Sequence_MD5', 'Dom_Domain_Count', 'DomQual']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for pdb_file in pdb_files_iter:
            processed_count += 1
            # Preserve original filename for reporting (extracted files keep their original names)
            found_files.add(Path(pdb_file).name)

            if processed_count % 100 == 0:
                print(f"Processed {processed_count} files...")

            pdb_chain_info = extract_pdb_chain_info(str(pdb_file))
            if not pdb_chain_info:
                print(f"Warning: No valid chains found in {Path(pdb_file).name}")
                continue

            domain_count = run_dom_analysis(str(pdb_file), dom_path)
            quality_score = quality_scores.get(Path(pdb_file).name, 0.0)
            quality_score_out = format_sigfigs(quality_score, 5)

            batch_results = []
            for pdb_id, chain_id, sequence_md5 in pdb_chain_info:
                batch_results.append({
                    'PDB_ID': pdb_id,
                    'Chain_ID': chain_id,
                    'Sequence_MD5': sequence_md5,
                    'Dom_Domain_Count': domain_count,
                    'DomQual': quality_score_out
                })
            writer.writerows(batch_results)
            results.extend(batch_results)
            if processed_count % batch_size == 0:
                csvfile.flush()

    print("\nProcessing complete!")
    print(f"Files processed: {processed_count}")
    print(f"Total entries written: {len(results)}")
    print(f"Results written to: {output_file}")
    # Clean up temporary extraction directory if used
    if temp_dir is not None:
        try:
            temp_dir.cleanup()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(
        description="Process PDB files to extract domain information and quality scores",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all PDB files in a directory
  %(prog)s -d /large/pdb/directory/ -o results.csv
  # Process all PDB files in a zip
  %(prog)s -z pdbs.zip -o results.csv
  # Process only a subset of files in a zip
  %(prog)s -z pdbs.zip --zip-list files_to_process.txt -o results.csv
        """
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-d', '--directory', help='Directory containing PDB files')
    group.add_argument('-z', '--zip', help='Zip file containing PDB files')
    parser.add_argument('--zip-list', help='Optional: file with list of PDB filenames to process from zip')
    parser.add_argument('-o', '--output', required=True, help='Output CSV file path')
    parser.add_argument('--dom-path', default=DEFAULT_DOM_PATH, help='Path to dom executable')
    parser.add_argument('--domqual-path', default=DEFAULT_DOMQUAL_PATH, help='Path to domqual Python script')
    parser.add_argument('--batch-size', type=int, default=1000, help='Number of files to process before flushing output (default: 1000)')
    args = parser.parse_args()

    if args.directory and not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist", file=sys.stderr)
        sys.exit(1)
    if args.zip and not os.path.isfile(args.zip):
        print(f"Error: Zip file '{args.zip}' does not exist", file=sys.stderr)
        sys.exit(1)
    if args.zip_list and not os.path.isfile(args.zip_list):
        print(f"Error: Zip list file '{args.zip_list}' does not exist", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.dom_path):
        print(f"Error: Dom executable '{args.dom_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.domqual_path):
        print(f"Error: DomQual script '{args.domqual_path}' does not exist", file=sys.stderr)
        sys.exit(1)

    try:
        process_pdb_inputs(
            args.directory,
            args.zip,
            args.zip_list,
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
