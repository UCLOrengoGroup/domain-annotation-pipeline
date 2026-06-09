import argparse
import io
import zipfile
from pathlib import Path
from urllib.parse import quote

import requests


DEFAULT_AFDB_BASE_URL = "https://alphafold.ebi.ac.uk/files"


def iter_ids(path: Path):
    for raw in path.read_text().splitlines():
        af_id = raw.strip().rstrip("\r")
        if not af_id or af_id.startswith("#"):
            continue
        yield af_id


def format_error(exc: Exception) -> tuple[str, str]:
    response = getattr(exc, "response", None)
    status_code = "-"
    if response is not None and getattr(response, "status_code", None) is not None:
        status_code = str(response.status_code)
    return status_code, f"{type(exc).__name__}: {exc}"


def write_log_row(handle, row: tuple[str, str, str, str, str, str]) -> None:
    handle.write("\t".join(row) + "\n")
    handle.flush()


def main() -> int:
    parser = argparse.ArgumentParser(description="Download AlphaFold BCIF files and package them into a zip.")
    parser.add_argument("--id-file", required=True, help="File with one AlphaFold ID per line")
    parser.add_argument("--base-url", default=DEFAULT_AFDB_BASE_URL, help="Base URL for AlphaFold BCIF downloads")
    parser.add_argument("--out-bcif-zip", required=True, help="Output zip file for downloaded BCIF files")
    args = parser.parse_args()

    id_file = Path(args.id_file)
    base_url = args.base_url.rstrip("/")
    out_bcif_zip = Path(args.out_bcif_zip)

    downloaded: list[str] = []
    failed: list[str] = []
    with Path("download_log.tsv").open("w", buffering=1) as log_handle, \
         zipfile.ZipFile(out_bcif_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        log_handle.write("af_id\turl\thttp_status\tbytes\tresult\terror\n")
        log_handle.flush()

        for af_id in iter_ids(id_file):
            url = f"{base_url}/{quote(af_id)}.bcif"

            if "/" in af_id:
                failed.append(af_id)
                write_log_row(log_handle, (af_id, url, "-", "0", "invalid_id", "ID contains '/'"))
                continue

            try:
                with requests.get(
                    url,
                    stream=True,
                    timeout=(15, 120),
                    headers={"User-Agent": "domain-annotation-pipeline/prepare_af_pdb_zip"},
                ) as response:
                    response.raise_for_status()
                    buf = io.BytesIO()
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            buf.write(chunk)
                    status_code = str(response.status_code)

                n_bytes = buf.tell()
                if n_bytes == 0:
                    failed.append(af_id)
                    write_log_row(log_handle, (af_id, url, status_code, "0", "empty_file", "downloaded file was empty"))
                    continue

                archive.writestr(f"{af_id}.bcif", buf.getvalue())
                downloaded.append(af_id)
                write_log_row(log_handle, (af_id, url, status_code, str(n_bytes), "downloaded", "-"))

            except Exception as exc:
                failed.append(af_id)
                status_code, error_text = format_error(exc)
                write_log_row(log_handle, (af_id, url, status_code, "0", "failed", error_text))

    Path("downloaded_ids.txt").write_text("\n".join(downloaded) + ("\n" if downloaded else ""))
    Path("failed_ids.txt").write_text("\n".join(failed) + ("\n" if failed else ""))
    Path("prep_summary.txt").write_text(f"downloaded\t{len(downloaded)}\nfailed\t{len(failed)}\n")

    if not downloaded:
        raise SystemExit("No BCIF files downloaded successfully")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
