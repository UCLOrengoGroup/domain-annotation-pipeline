#!/usr/bin/env python3
"""
Download tar archives from Google Drive folder, decompress, and convert to zip files.
Supports caching and resume functionality.
"""

import os
import sys
import tarfile
import zipfile
import subprocess
import hashlib
import json
from pathlib import Path
from datetime import datetime

import gdown

# Google Drive folder ID from the URL you provided
FOLDER_ID = "12rlP_a9IQAnwRvfHTpEmkVDccDa780wi"

class CacheManager:
    """Manages caching state for downloads and conversions"""
    
    def __init__(self, cache_dir):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / 'processing_cache.json'
        self.cache_data = self.load_cache()
    
    def load_cache(self):
        """Load cache data from file"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load cache file: {e}")
        return {}
    
    def save_cache(self):
        """Save cache data to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache file: {e}")
    
    def get_file_hash(self, file_path):
        """Calculate MD5 hash of file for integrity checking"""
        if not Path(file_path).exists():
            return None
        
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
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
        current_size = file_path.stat().st_size
        
        # Verify file integrity (skip hash for large files to save time)
        return (
            cached_info.get('status') == 'complete' and
            cached_info.get('size') == current_size and
            current_size > 0
        )
    
    def mark_download_complete(self, file_id, file_path):
        """Mark download as complete with metadata"""
        file_path = Path(file_path)
        cache_key = f"download_{file_id}"
        
        self.cache_data[cache_key] = {
            'status': 'complete',
            'timestamp': datetime.now().isoformat(),
            'size': file_path.stat().st_size,
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
        tar_mtime = tar_path.stat().st_mtime
        zip_size = zip_path.stat().st_size
        
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
        cache_key = f"conversion_{tar_path.name}"
        
        self.cache_data[cache_key] = {
            'status': 'complete',
            'timestamp': datetime.now().isoformat(),
            'tar_path': str(tar_path),
            'tar_mtime': tar_path.stat().st_mtime,
            'tar_size': tar_path.stat().st_size,
            'zip_path': str(zip_path),
            'zip_size': zip_path.stat().st_size
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
        return True
    except Exception as e:
        print(f"Folder download failed: {e}")
        return False

def find_tar_files(directory):
    """Find all tar files in directory recursively"""
    directory = Path(directory)
    tar_files = []
    
    # Look for various tar file extensions
    for pattern in ['*.tar', '*.tar.gz', '*.tar.bz2', '*.tar.xz']:
        tar_files.extend(directory.rglob(pattern))
    
    return tar_files

def download_from_google_drive(file_id, output_path, cache_manager, force=False):
    """Download file from Google Drive using file ID with caching"""
    output_path = Path(output_path)
    
    # Check cache unless forced
    if not force and cache_manager.is_download_complete(file_id, output_path):
        print(f"✓ Download cached: {output_path.name} (skipping)")
        return True
    
    url = f"https://drive.google.com/uc?id={file_id}"
    print(f"Downloading {file_id} to {output_path}")
    
    try:
        # Remove incomplete file if exists
        if output_path.exists():
            output_path.unlink()
        
        gdown.download(url, str(output_path), quiet=False)
        
        # Verify download
        if output_path.exists() and output_path.stat().st_size > 0:
            cache_manager.mark_download_complete(file_id, output_path)
            print(f"✓ Download complete: {output_path.name}")
            return True
        else:
            print(f"✗ Download failed: {output_path.name} (file empty or missing)")
            return False
            
    except Exception as e:
        print(f"✗ Error downloading {file_id}: {e}")
        # Clean up partial file
        if output_path.exists():
            output_path.unlink()
        return False

def extract_tar_to_zip(tar_path, output_dir, cache_manager, force=False):
    """Extract tar file and create zip file with caching"""
    tar_path = Path(tar_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
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
    
    try:
        # Remove incomplete zip if exists
        if zip_path.exists():
            zip_path.unlink()
        
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
                        if file_data:
                            # Add to zip with same path structure
                            zip_file.writestr(member.name, file_data.read())
                            processed_files += 1
                            
                            # Progress indicator (less verbose)
                            if processed_files % 1000 == 0 or processed_files == total_files:
                                print(f"  Progress: {processed_files}/{total_files} files")
        
        # Verify conversion
        if zip_path.exists() and zip_path.stat().st_size > 0:
            cache_manager.mark_conversion_complete(tar_path, zip_path)
            
            # Show size comparison
            tar_size = tar_path.stat().st_size / (1024*1024)  # MB
            zip_size = zip_path.stat().st_size / (1024*1024)  # MB
            compression_ratio = (1 - zip_size/tar_size) * 100 if tar_size > 0 else 0
            
            print(f"✓ Conversion complete: {zip_path.name}")
            print(f"  Size: {tar_size:.1f}MB → {zip_size:.1f}MB ({compression_ratio:.1f}% compression)")
            return zip_path
        else:
            print(f"✗ Conversion failed: {zip_path.name} (file empty or missing)")
            return None
        
    except Exception as e:
        print(f"✗ Error converting {tar_path.name}: {e}")
        # Clean up partial zip
        if zip_path.exists():
            zip_path.unlink()
        return None

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
    
    # Parse command line arguments
    force_download = '--force-download' in sys.argv
    force_conversion = '--force-conversion' in sys.argv
    force_all = '--force-all' in sys.argv
    use_file_list = '--use-file-list' in sys.argv
    
    if force_all:
        force_download = force_conversion = True
    
    # Try to download entire folder
    print("\n1. Attempting to download entire Google Drive folder...")
    
    if download_folder_from_google_drive(FOLDER_ID, download_dir):
        print("✓ Folder download successful!")
        
        # Find all tar files in downloaded content
        tar_files = find_tar_files(download_dir)
        print(f"Found {len(tar_files)} tar files:")
        for tar_file in tar_files:
            print(f"  - {tar_file.name}")
        
        # Convert each tar file to zip
        successful_conversions = 0
        for i, tar_file in enumerate(tar_files, 1):
            print(f"\n[{i}/{len(tar_files)}] Processing {tar_file.name}...")
            
            zip_path = extract_tar_to_zip(tar_file, output_dir, cache_manager, force_conversion)
            if zip_path:
                successful_conversions += 1
        
        print(f"\n✓ Folder method: {successful_conversions}/{len(tar_files)} conversions successful")
        
    else:
        raise RuntimeError("✗ Folder download failed")

    
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
    
    print(f"\nCache location: {cache_dir.absolute()}")
    print("\nUsage options:")
    print("  python prepare_bfvd_esm_data.py                 # Try folder download first, fallback to file list")
    print("  python prepare_bfvd_esm_data.py --force-all     # Force redownload and reconvert everything")

if __name__ == "__main__":
    main()