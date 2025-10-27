#!/usr/bin/env python3
"""
Download tar archives from Google Drive folder, decompress, and convert to zip files.
Supports both regular PDB archives and foldcomp archives.
Supports caching and resume functionality.
"""

import os
import sys
import tarfile
import zipfile
import subprocess
import hashlib
import json
import re
import shutil
from pathlib import Path
from datetime import datetime

import gdown

# Google Drive folder ID from the URL you provided
FOLDER_ID = "12rlP_a9IQAnwRvfHTpEmkVDccDa780wi"

class CacheError(Exception):
    """Exception raised for cache-related errors"""
    pass

class DownloadError(Exception):
    """Exception raised for download-related errors"""
    pass

class ConversionError(Exception):
    """Exception raised for archive conversion errors"""
    pass

class FoldcompError(Exception):
    """Exception raised for foldcomp-related errors"""
    pass

class CacheManager:
    """Manages caching state for downloads and conversions"""
    
    def __init__(self, cache_dir):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / 'processing_cache.json'
        self.cache_data = self.load_cache()
    
    def load_cache(self):
        """Load cache data from file"""
        if not self.cache_file.exists():
            return {}
        
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, OSError) as e:
            raise CacheError(f"Failed to load cache file {self.cache_file}: {e}") from e
    
    def save_cache(self):
        """Save cache data to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache_data, f, indent=2)
        except (IOError, OSError) as e:
            raise CacheError(f"Failed to save cache file {self.cache_file}: {e}") from e
    
    def get_file_hash(self, file_path):
        """Calculate MD5 hash of file for integrity checking"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found for hashing: {file_path}")
        
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (IOError, OSError) as e:
            raise CacheError(f"Failed to calculate hash for {file_path}: {e}") from e
    
    def is_download_complete(self, file_id, file_path):
        """Check if download is complete and valid"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False
        
        # Check if we have cached info for this file
        cache_key = f"download_{file_id}"
        if cache_key not in self.cache_data:
            return False
        
        cached_info = self.cache_data[cache_key]
        try:
            current_size = file_path.stat().st_size
        except OSError as e:
            raise CacheError(f"Failed to get file stats for {file_path}: {e}") from e
        
        # Verify file integrity (skip hash for large files to save time)
        return (
            cached_info.get('status') == 'complete' and
            cached_info.get('size') == current_size and
            current_size > 0
        )
    
    def mark_download_complete(self, file_id, file_path):
        """Mark download as complete with metadata"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Cannot mark non-existent file as downloaded: {file_path}")
        
        cache_key = f"download_{file_id}"
        
        try:
            file_size = file_path.stat().st_size
        except OSError as e:
            raise CacheError(f"Failed to get file stats for {file_path}: {e}") from e
        
        self.cache_data[cache_key] = {
            'status': 'complete',
            'timestamp': datetime.now().isoformat(),
            'size': file_size,
            'path': str(file_path)
        }
        self.save_cache()
    
    def is_conversion_complete(self, tar_path, zip_path):
        """Check if conversion is complete and valid"""
        tar_path = Path(tar_path)
        zip_path = Path(zip_path)
        
        if not zip_path.exists():
            return False
        
        cache_key = f"conversion_{tar_path.name}"
        if cache_key not in self.cache_data:
            return False
        
        cached_info = self.cache_data[cache_key]
        
        try:
            tar_mtime = tar_path.stat().st_mtime
            zip_size = zip_path.stat().st_size
        except OSError as e:
            raise CacheError(f"Failed to get file stats for cache validation: {e}") from e
        
        # Check if conversion is up to date
        return (
            cached_info.get('status') == 'complete' and
            cached_info.get('tar_mtime') == tar_mtime and
            cached_info.get('zip_size') == zip_size and
            zip_size > 0
        )
    
    def mark_conversion_complete(self, tar_path, zip_path):
        """Mark conversion as complete with metadata"""
        tar_path = Path(tar_path)
        zip_path = Path(zip_path)
        
        if not tar_path.exists():
            raise FileNotFoundError(f"Source tar file not found: {tar_path}")
        if not zip_path.exists():
            raise FileNotFoundError(f"Output zip file not found: {zip_path}")
        
        cache_key = f"conversion_{tar_path.name}"
        
        try:
            tar_stat = tar_path.stat()
            zip_stat = zip_path.stat()
        except OSError as e:
            raise CacheError(f"Failed to get file stats for cache marking: {e}") from e
        
        self.cache_data[cache_key] = {
            'status': 'complete',
            'timestamp': datetime.now().isoformat(),
            'tar_path': str(tar_path),
            'tar_mtime': tar_stat.st_mtime,
            'tar_size': tar_stat.st_size,
            'zip_path': str(zip_path),
            'zip_size': zip_stat.st_size
        }
        self.save_cache()

def download_folder_from_google_drive(folder_id, output_dir):
    """Download entire folder from Google Drive"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Attempting to download entire folder {folder_id}...")
    
    try:
        # Download entire folder
        gdown.download_folder(
            f"https://drive.google.com/drive/folders/{folder_id}",
            output=str(output_dir),
            quiet=False,
            use_cookies=False
        )
        print("✓ Folder download successful!")
    except Exception as e:
        raise DownloadError(f"Google Drive folder download failed for folder {folder_id}: {e}") from e

def find_tar_files(directory):
    """Find all tar files in directory recursively"""
    directory = Path(directory)
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    tar_files = []
    
    # Look for various tar file extensions
    for pattern in ['*.tar', '*.tar.gz', '*.tar.bz2', '*.tar.xz']:
        tar_files.extend(directory.rglob(pattern))
    
    return tar_files

def is_foldcomp_archive(filename):
    """Check if the archive is a foldcomp archive based on filename"""
    return "_foldcomp" in str(filename).lower()

def check_foldcomp_available():
    """Check if foldcomp command is available"""
    try:
        result = subprocess.run(['foldcomp', '--help'], 
                              capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        raise FoldcompError("foldcomp command timed out during availability check")
    except FileNotFoundError:
        return False

def extract_bfvd_id_from_filename(filename):
    """Extract BFVD ID from filename"""
    base_name = Path(filename).stem
    regex = r'(MGY[0-9A-Z]+)'
    match = re.search(regex, base_name)
    if match:
        return match.group(1)
    raise ValueError(f"Could not extract BFVD ID from filename: {base_name} ({regex})")

def decompress_foldcomp_archive(tar_path, temp_dir):
    """Decompress foldcomp archive to PDB files"""
    temp_dir = Path(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"  Decompressing foldcomp archive: {tar_path.name}")
    
    try:
        # Run foldcomp decompress
        foldcomp_args = ['foldcomp', 'decompress', str(tar_path), str(temp_dir)] 
        result = subprocess.run(
            foldcomp_args,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout for large archives
        )
        
        if result.returncode != 0:
            raise FoldcompError(f"foldcomp failed with return code {result.returncode}: "
                              f"Command: {' '.join(foldcomp_args)}, STDERR: {result.stderr}")
        
        # Find all generated PDB files
        pdb_files = list(temp_dir.rglob("*.pdb"))
        if not pdb_files:
            raise FoldcompError(f"No PDB files generated from foldcomp decompression of {tar_path}")
        
        print(f"  Generated {len(pdb_files)} PDB files")
        return pdb_files
        
    except subprocess.TimeoutExpired:
        raise FoldcompError(f"foldcomp decompress timed out after 1 hour for {tar_path}")

def extract_tar_to_zip(tar_path, output_dir, cache_manager, force=False):
    """Extract tar file and create zip file with caching"""
    tar_path = Path(tar_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not tar_path.exists():
        raise FileNotFoundError(f"Source tar file not found: {tar_path}")
    
    # Create zip filename
    zip_name = tar_path.stem
    if tar_path.suffix == '.gz' and tar_path.stem.endswith('.tar'):
        zip_name = tar_path.stem[:-4]  # Remove .tar from .tar.gz
    
    zip_path = output_dir / f"{zip_name}.zip"
    
    # Check cache unless forced
    if not force and cache_manager.is_conversion_complete(tar_path, zip_path):
        print(f"✓ Conversion cached: {zip_path.name} (skipping)")
        return zip_path
    
    print(f"Converting {tar_path.name} to {zip_path.name}")
    
    # Check if this is a foldcomp archive
    is_foldcomp = is_foldcomp_archive(tar_path.name)
    
    if is_foldcomp:
        print(f"  Detected foldcomp archive")
        
        # Check if foldcomp is available
        if not check_foldcomp_available():
            raise FoldcompError("foldcomp command not found. Please install foldcomp.")
        
        # Create temporary directory for foldcomp decompression
        temp_dir = Path.cwd() / 'temp_foldcomp' / tar_path.stem
        try:
            # Remove incomplete zip if exists
            if zip_path.exists():
                zip_path.unlink()
            
            # Decompress using foldcomp
            pdb_files = decompress_foldcomp_archive(tar_path, temp_dir)
            
            # Create zip from decompressed PDB files
            try:
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zip_file:
                    total_files = len(pdb_files)
                    processed_files = 0
                    
                    print(f"  Zipping {total_files} PDB files...")
                    
                    for pdb_file in pdb_files:
                        # Use the filename as-is, or extract BFVD ID if needed
                        pdb_filename = pdb_file.name
                        
                        try:
                            # Read and add to zip
                            with open(pdb_file, 'rb') as f:
                                zip_file.writestr(pdb_filename, f.read())
                            
                            processed_files += 1
                            
                            # Progress indicator
                            if processed_files % 1000 == 0 or processed_files == total_files:
                                print(f"    Progress: {processed_files}/{total_files} files")
                                
                        except (IOError, OSError) as e:
                            raise ConversionError(f"Failed to add {pdb_file.name} to zip: {e}") from e
                            
            except (zipfile.BadZipFile, IOError, OSError) as e:
                raise ConversionError(f"Failed to create zip file {zip_path}: {e}") from e
            
        finally:
            # Clean up temporary directory
            if temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except OSError as e:
                    print(f"Warning: Failed to clean up temporary directory {temp_dir}: {e}")
    
    else:
        # Regular tar archive with PDB files
        print(f"  Processing regular tar archive")
        
        # Remove incomplete zip if exists
        if zip_path.exists():
            zip_path.unlink()
        
        try:
            # Open tar file and create zip file
            with tarfile.open(tar_path, 'r:*') as tar_file:
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zip_file:
                    members = tar_file.getmembers()
                    total_files = len([m for m in members if m.isfile()])
                    processed_files = 0
                    
                    print(f"  Processing {total_files} files...")
                    
                    for member in members:
                        if member.isfile():
                            # Extract file data from tar
                            file_data = tar_file.extractfile(member)
                            if file_data is None:
                                raise ConversionError(f"Failed to extract {member.name} from tar archive")

                            bfvd_id = extract_bfvd_id_from_filename(member.name)
                            pdb_filename = f"{bfvd_id}.pdb"
                            
                            # Add to zip
                            zip_file.writestr(pdb_filename, file_data.read())
                            processed_files += 1
                            
                            # Progress indicator
                            if processed_files % 1000 == 0 or processed_files == total_files:
                                print(f"    Progress: {processed_files}/{total_files} files")
                        
        except (tarfile.TarError, zipfile.BadZipFile, IOError, OSError) as e:
            # Clean up partial zip
            if zip_path.exists():
                zip_path.unlink()
            raise ConversionError(f"Error processing regular archive {tar_path.name}: {e}") from e
    
    # Verify conversion
    if not zip_path.exists():
        raise ConversionError(f"Conversion failed: output file {zip_path.name} was not created")
    
    zip_size = zip_path.stat().st_size
    if zip_size == 0:
        zip_path.unlink()  # Remove empty file
        raise ConversionError(f"Conversion failed: output file {zip_path.name} is empty")
    
    # Mark as complete in cache
    cache_manager.mark_conversion_complete(tar_path, zip_path)
    
    # Show size comparison
    tar_size = tar_path.stat().st_size / (1024*1024)  # MB
    zip_size_mb = zip_size / (1024*1024)  # MB
    compression_ratio = (1 - zip_size_mb/tar_size) * 100 if tar_size > 0 else 0
    
    print(f"✓ Conversion complete: {zip_path.name}")
    print(f"  Size: {tar_size:.1f}MB → {zip_size_mb:.1f}MB ({compression_ratio:.1f}% compression)")
    print(f"  Type: {'Foldcomp' if is_foldcomp else 'Regular'} archive")
    return zip_path

def main():
    """Main processing function"""
    # Configuration
    download_dir = Path('./downloads')
    output_dir = Path('./zip_files')
    cache_dir = Path('./cache')
    
    # Create directories
    download_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    cache_dir.mkdir(exist_ok=True)
    
    # Initialize cache manager
    cache_manager = CacheManager(cache_dir)
    
    print("=" * 60)
    print("BFVD ESM Data Preparation")
    print("=" * 60)
    
    # Check if foldcomp is available
    if check_foldcomp_available():
        print("✓ foldcomp command found")
    else:
        print("⚠ foldcomp command not found - foldcomp archives will fail")
    
    # Parse command line arguments
    force_download = '--force-download' in sys.argv
    force_conversion = '--force-conversion' in sys.argv
    force_all = '--force-all' in sys.argv
    
    if force_all:
        force_download = force_conversion = True
    
    # Try to download entire folder
    print("\n1. Attempting to download entire Google Drive folder...")
    
    download_folder_from_google_drive(FOLDER_ID, download_dir)
    
    # Find all tar files in downloaded content
    tar_files = find_tar_files(download_dir)
    if not tar_files:
        raise DownloadError("No tar files found in downloaded content")
    
    print(f"Found {len(tar_files)} tar files:")
    
    # Categorize files
    foldcomp_files = []
    regular_files = []
    
    for tar_file in tar_files:
        if is_foldcomp_archive(tar_file.name):
            foldcomp_files.append(tar_file)
            print(f"  - {tar_file.name} (foldcomp)")
        else:
            regular_files.append(tar_file)
            print(f"  - {tar_file.name} (regular)")
    
    print(f"\nArchive summary: {len(foldcomp_files)} foldcomp, {len(regular_files)} regular")
    
    # Convert each tar file to zip
    successful_conversions = 0
    failed_conversions = []
    
    for i, tar_file in enumerate(tar_files, 1):
        print(f"\n[{i}/{len(tar_files)}] Processing {tar_file.name}...")
        
        try:
            zip_path = extract_tar_to_zip(tar_file, output_dir, cache_manager, force_conversion)
            if zip_path:
                successful_conversions += 1
        except Exception as e:
            failed_conversions.append((tar_file.name, str(e)))
            print(f"✗ Failed to process {tar_file.name}: {e}")
            continue
    
    print(f"\n✓ Conversion results: {successful_conversions}/{len(tar_files)} successful")
    
    if failed_conversions:
        print(f"\n✗ Failed conversions ({len(failed_conversions)}):")
        for filename, error in failed_conversions:
            print(f"  - {filename}: {error}")

    # Final summary
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE")
    print("=" * 60)
    
    # Show output files
    zip_files = list(output_dir.glob("*.zip"))
    if zip_files:
        total_size = sum(f.stat().st_size for f in zip_files) / (1024*1024*1024)  # GB
        print(f"Output: {len(zip_files)} zip files ({total_size:.2f}GB total)")
        print(f"Location: {output_dir.absolute()}")
        
        print("\nCreated files:")
        for zip_file in sorted(zip_files):
            size_mb = zip_file.stat().st_size / (1024*1024)
            print(f"  - {zip_file.name} ({size_mb:.1f}MB)")
    else:
        print("⚠ No output files created")
    
    print(f"\nCache location: {cache_dir.absolute()}")
    print("\nRequirements:")
    print("  - foldcomp command for processing foldcomp archives")
    print("  - Install: https://github.com/steineggerlab/foldcomp")
    
    # Raise exception if any critical failures occurred
    if failed_conversions and successful_conversions == 0:
        raise ConversionError(f"All {len(failed_conversions)} conversions failed")

if __name__ == "__main__":
    main()