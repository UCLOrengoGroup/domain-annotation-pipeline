import argparse
import re
import csv
import io
import time
import json
import math
import requests
import pandas as pd
from requests.adapters import HTTPAdapter, Retry

TOOL_NAME = "domain-annotation-pipeline"
TOOL_EMAIL = "i.sillitoe@ucl.ac.uk"
MISSING_VALUE = pd.NA

API_URL = "https://rest.uniprot.org"
POLLING_INTERVAL = 3  # seconds

# UniProt accession-ish regex (classic + extended)
UNIPROT_ACC_RE = re.compile(r'^[A-Z0-9]{6,10}$')

# Session with retries on transient errors
session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504],
)
session.mount("https://", HTTPAdapter(max_retries=retries))


def clean_accessions(accessions):
    """Strip whitespace, drop obvious headers/garbage, keep only valid-looking accessions."""
    clean = []
    for a in accessions:
        a = a.strip()
        if not a:
            continue
        if a.lower() in {"uniprot_id", "accession", "id"}:
            continue
        if not UNIPROT_ACC_RE.match(a):
            # Debug only if you like:
            print(f"[WARN] Skipping invalid accession candidate: {a!r}")
            continue
        clean.append(a)

    if not clean:
        raise ValueError("No valid UniProt accessions after cleaning input")

    return clean


def submit_id_mapping(ids):
    """Submit an ID mapping job: UniProtKB_AC-ID -> UniProtKB."""
    data = {
        "from": "UniProtKB_AC-ID",
        "to": "UniProtKB",
        "ids": ",".join(ids),
    }
    print(f"[INFO]   Submitting ID mapping job for {len(ids)} IDs...")
    resp = session.post(f"{API_URL}/idmapping/run", data=data)
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        print("[ERROR]   Failed to submit ID mapping job")
        try:
            print(json.dumps(resp.json(), indent=2)[:1000])
        except Exception:
            print(resp.text[:1000])
        raise

    job = resp.json()
    job_id = job.get("jobId")
    if not job_id:
        raise RuntimeError(f"ID mapping submission did not return jobId: {job}")
    print(f"[INFO]   Job ID: {job_id}")
    return job_id


def wait_for_job(job_id, poll_interval=POLLING_INTERVAL, max_wait=600):
    """Poll job status until finished or error."""
    start = time.time()
    attempt = 0
    retries = 0
    max_retries = 3
    while retries < max_retries:
        while True:
            attempt += 1
            try:
                resp = session.get(f"{API_URL}/idmapping/status/{job_id}")
                resp.raise_for_status()
            except requests.RequestException as e:
                print(f"[ERROR]   Exception during status check for job {job_id}: {e}")
                time.sleep(2 ** retries)
                retries += 1
                break  # break inner while, retry outer while
            status = resp.json()
            if "jobStatus" in status:
                state = status["jobStatus"]
                print(f"[INFO]   Job {job_id} status: {state} (check {attempt})")
                if state == "RUNNING":
                    if time.time() - start > max_wait:
                        raise TimeoutError(f"Job {job_id} did not finish within {max_wait} seconds")
                    time.sleep(poll_interval)
                    continue
                else:
                    # Any other jobStatus is an error condition
                    print(f"[ERROR]   Status check failed for job {job_id}")
                    print(json.dumps(status, indent=2)[:1000])
                    time.sleep(2 ** retries)
                    retries += 1
                    break  # break inner while, retry outer while
            else:
                # No jobStatus field -> results/failedIds present: finished
                print(f"[INFO]   Job {job_id} finished.")
                return
    # If we get here, all retries failed
    raise RuntimeError(f"Job {job_id} failed after {max_retries} retries.")


def download_mapping_results(job_id):
    """
    Download all mapping results as TSV with enrichment fields.

    We request:
      accession      -> Entry
      organism_id    -> Organism ID
      organism_name  -> Organism
      lineage        -> Taxonomic lineage (all)
    """
    params = {
        "format": "tsv",
        "fields": "accession,organism_id,organism_name,lineage",
        "size": 500,
    }
    print(f"[INFO]   Downloading results for job {job_id} with pagination...")
    print(f"[INFO]   Params: {params}")
    endpoint = f"{API_URL}/idmapping/uniprotkb/results/stream/{job_id}"
    all_lines = []
    cursor = None
    batch = 0
    while True:
        batch += 1
        if cursor:
            params["cursor"] = cursor
        else:
            params.pop("cursor", None)
        print(f"[INFO]   Fetching batch {batch} with params: {params}...")
        resp = session.get(endpoint, params=params)
        try:
            resp.raise_for_status()
        except requests.HTTPError:
            print(f"[ERROR]   Failed to download results for job {job_id} (batch {batch})")
            try:
                print(json.dumps(resp.json(), indent=2)[:1000])
            except Exception:
                print(resp.text[:1000])
            raise
        lines = resp.text.splitlines()
        if batch == 1:
            print("[DEBUG] First 10 lines of first batch:")
            for line in lines[:10]:
                print(line)
        if not lines or (batch > 1 and len(lines) == 1):
            break
        if batch == 1:
            all_lines.extend(lines)
        else:
            # Skip header for subsequent batches
            all_lines.extend(lines[1:])
        # Check for pagination cursor in headers
        cursor = resp.headers.get("Link")
        if not cursor:
            break
    print(f"[INFO]   Downloaded {len(all_lines)} lines in {batch} batch(es)")
    return "\n".join(all_lines)


def parse_mapping_tsv(tsv_text):
    """
    Parse the TSV returned by ID mapping into a dict keyed by input accession.

    Expected columns (labels):
      From                        -> input accession
      Entry                       -> UniProt accession
      Organism ID                 -> taxon ID
      Organism                    -> organism name
      Taxonomic lineage (all)     -> lineage
    """
    by_input = {}
    f = io.StringIO(tsv_text)
    reader = csv.DictReader(f, delimiter="\t")

    for row in reader:
        from_id = row.get("From") or row.get("from")  # input ID
        if not from_id:
            # Fallback: use Entry if From is missing (shouldn't happen, but belt & braces)
            from_id = row.get("Entry") or row.get("accession")
        if not from_id:
            continue

        entry_acc = row.get("Entry") or row.get("accession") or ""
        tax_id = row.get("Organism (ID)") or row.get("Organism ID") or row.get("organism_id") or ""
        org_name = row.get("Organism") or row.get("organism_name") or ""
        lineage = row.get("Taxonomic lineage") or row.get("Taxonomic lineage (all)") or row.get("Taxonomic lineage (ALL)") or row.get("lineage") or ""

        by_input[from_id] = {
            "entry": entry_acc,
            "tax_id": tax_id,
            "organism_name": org_name,
            "lineage": lineage,
        }

    return by_input


def fetch_uniprot_batch(accessions):
    """
    Batch version of your old per-accession logic, using ID mapping.

    Returns list of dicts with keys:
      accession, proteome_id, tax_common_name, tax_scientific_name, tax_lineage
    """
    ids = clean_accessions(accessions)
    print(f"[INFO] Processing batch of {len(ids)} IDs")

    # Submit mapping job with retry logic
    max_submit_retries = 3
    for submit_attempt in range(max_submit_retries):
        try:
            job_id = submit_id_mapping(ids)
            wait_for_job(job_id)
            break
        except Exception as e:
            print(f"[ERROR]   Failed to submit or process job (attempt {submit_attempt+1}/{max_submit_retries}): {e}")
            if submit_attempt < max_submit_retries - 1:
                time.sleep(2 ** submit_attempt)
            else:
                print("[ERROR]   Skipping this batch due to repeated failures.")
                return []
    else:
        # If we exited the loop without setting job_id, skip batch
        print("[ERROR]   Could not obtain job_id, skipping batch.")
        return []
    tsv_text = download_mapping_results(job_id)
    mapped = parse_mapping_tsv(tsv_text)

    rows = []

    for acc in ids:
        entry = mapped.get(acc)
        if entry is None:
            rows.append({
                "accession": acc,
                "proteome_id": "",
                "tax_common_name": "",
                "tax_scientific_name": "",
                "tax_lineage": "",
            })
            continue

        tax_id = entry["tax_id"]
        lineage = entry["lineage"]
        organism = entry["organism_name"]

        # Match your old synthetic proteome_id logic
        proteome_id = f"proteome-tax_id-{tax_id}-0_v4" if tax_id else ""

        # Human special case
        if tax_id == "9606":
            tax_common_name = "Human"
            tax_scientific_name = "Homo sapiens"
        # Try to split on parentheses: e.g. 'Human (Homo sapiens)'
        elif organism and "(" in organism and ")" in organism:
            try:
                common, sci = organism.split("(", 1)
                tax_common_name = common.strip()
                tax_scientific_name = sci.strip(") ")
            except Exception:
                tax_common_name = ""
                tax_scientific_name = organism
        else:
            tax_common_name = ""
            tax_scientific_name = organism

        rows.append({
            "accession": acc,
            "proteome_id": proteome_id,
            "tax_common_name": tax_common_name,
            "tax_scientific_name": tax_scientific_name,
            "tax_lineage": lineage.replace(";", ";"),
        })

    return rows



def fetch_uniprot_info(accession):
    """Fetch UniProt taxonomy and proteome metadata for a given accession."""
    url = f"https://rest.uniprot.org/uniprotkb/search?query=accession:{accession}&fields=xref_proteomes,organism_name&format=json"
    response = requests.get(url)
    data = response.json()
    
    try:
        result = data['results'][0]
        # proteome_id = proteome_info.get('id', '')  # Unused variable, remove
        tax_id = result['organism']['taxonId']
        lineage = result['organism']['lineage']
        return {
            "accession": accession,
            "proteome_id": f"proteome-tax_id-{tax_id}-0_v4",
            "tax_common_name": result['organism'].get('commonName', ''),
            "tax_scientific_name": result['organism'].get('scientificName', ''),
            "tax_lineage": ';'.join(lineage)
        }
    except (IndexError, KeyError) as e:
        print(f"Failed to parse data for {accession}: {e}")
        return {
            "accession": accession,
            "proteome_id": MISSING_VALUE,
            "tax_common_name": MISSING_VALUE,
            "tax_scientific_name": MISSING_VALUE,
            "tax_lineage": MISSING_VALUE
        }

def run(accessions, out_path, batch_size=10000):
    accessions = [a.strip() for a in accessions if a.strip()]
    total = len(accessions)
    n_batches = math.ceil(total / batch_size)

    print(f"[INFO] Total accessions: {total}")
    print(f"[INFO] Batch size: {batch_size}")
    print(f"[INFO] Number of batches: {n_batches}")

    header = [
        "accession",
        "proteome_id",
        "tax_common_name",
        "tax_scientific_name",
        "tax_lineage",
    ]

    with open(out_path, "w") as out_f:
        out_f.write("\t".join(header) + "\n")

        for i in range(0, total, batch_size):
            batch_idx = i // batch_size + 1
            batch = accessions[i : i + batch_size]
            print(f"[INFO] === Batch {batch_idx}/{n_batches} ===")
            print(f"[INFO]   IDs in this batch: {len(batch)}")

            rows = fetch_uniprot_batch(batch)

            for row in rows:
                out_f.write("\t".join([
                    row["accession"],
                    row["proteome_id"],
                    row["tax_common_name"],
                    row["tax_scientific_name"],
                    row["tax_lineage"],
                ]) + "\n")

    print(f"[INFO] Done. Wrote output to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch taxonomy and proteome info from UniProt")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-a', '--accession', help='Comma-separated list of UniProt accessions')
    group.add_argument('-i', '--input', help='Input file with one UniProt accession per line')
    parser.add_argument('-o', '--output', required=True, help='Output TSV file path')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for UniProt queries (default: 1000)')
    args = parser.parse_args()

    import re
    uniprot_pattern = re.compile(r'^[A-NR-Z][0-9][A-Z0-9]{3}[0-9]$|^[OPQ][0-9][A-Z0-9]{3}[0-9]$|^[A-Z0-9]{1,2}[0-9][A-Z0-9]{2}[0-9]{3}$')

    if args.input:
        with open(args.input) as f:
            accessions = [line.strip() for line in f if line.strip()]
    elif args.accession:
        accessions = [a.strip() for a in args.accession.split(',') if a.strip()]
        # Validate each accession
        invalid = [a for a in accessions if not uniprot_pattern.match(a)]
        if invalid:
            print(f"Error: The following accessions are not valid UniProt accessions: {', '.join(invalid)}")
            exit(1)
    else:
        accessions = []

    run(accessions, args.output, batch_size=args.batch_size)
