import shutil
import gemmi
import tempfile
import zipfile
import sys
from pathlib import Path    

input_zip = Path(sys.argv[1])
output_zip = Path(sys.argv[2])

with zipfile.ZipFile(input_zip, "r") as zin, zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zout:
    for member in zin.infolist():
        name = member.filename
        if not name.endswith(".cif.gz"):
            continue
        base_name = Path(name).name[:-7]   # remove .cif.gz
        pdb_name = f"{base_name}.pdb"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            cif_path = tmpdir / f"{base_name}.cif.gz"
            pdb_path = tmpdir / pdb_name                
            # Extract one cif.gz member only
            with zin.open(member) as src, open(cif_path, "wb") as dst:
                shutil.copyfileobj(src, dst)                
            # Convert one file                
            structure = gemmi.read_structure(str(cif_path))
            structure.write_pdb(str(pdb_path))
            # Add converted pdb to output zip
            zout.write(pdb_path, arcname=pdb_name)
