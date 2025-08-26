import click

# Threshold constants
H_EVALUE_THRESHOLD = 0.019000
H_COVERAGE_THRESHOLD = 0.366757
H_TMSCORE_THRESHOLD = 0.560000
T_EVALUE_THRESHOLD = 0.108662
T_COVERAGE_THRESHOLD = 0.786333
T_TMSCORE_THRESHOLD = 0.416331

@click.command()
@click.option('--input', '-i', 'input_file', required=True, type=click.Path(exists=True),
              help='Path to the Foldseek output file.')
@click.option('--output', '-o', 'output_file', required=True, type=click.Path(),
              help='File to write the parsed results.')
def process_foldseek(input_file, output_file):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        current_query_hits = []
        current_query_id = None

        for line in infile:
            recs = line.strip().split()
            if len(recs) < 8:
                continue

            query_id, target_id, evalue, qlen, tlen, qtmscore, ttmscore = parse_record(recs)

            if current_query_id is None:
                current_query_id = query_id

            if query_id != current_query_id:
                best_hit = determine_best_hit(current_query_hits)
                if best_hit:
                    write_best_hit(outfile, current_query_id, best_hit)
                current_query_hits = []
                current_query_id = query_id

            update_hits(current_query_hits, target_id, evalue, qlen, tlen, qtmscore, ttmscore)

        if current_query_hits:
            best_hit = determine_best_hit(current_query_hits)
            if best_hit:
                write_best_hit(outfile, current_query_id, best_hit)

def parse_record(record):
    query_id, target_id = record[0], record[1]
    evalue, qlen, tlen, qtmscore, ttmscore = map(float, record[3:8])
    return query_id, target_id, evalue, int(qlen), int(tlen), qtmscore, ttmscore

def update_hits(current_query_hits, target_id, evalue, qlen, tlen, qtmscore, ttmscore):
    coverage = min(qlen, tlen) / max(qlen, tlen)
    tmscore = max(qtmscore, ttmscore)
    hit_type = determine_hit_type(evalue, coverage, tmscore)
    code = determine_code(target_id, hit_type)

    current_query_hits.append({
        'code': code,
        'evalue': evalue,
        'coverage': coverage,
        'tmscore': tmscore,
        'type': hit_type
    })

def determine_hit_type(evalue, coverage, tmscore):
    if evalue < H_EVALUE_THRESHOLD and coverage > H_COVERAGE_THRESHOLD and tmscore > H_TMSCORE_THRESHOLD:
        return 'H'
    elif evalue < T_EVALUE_THRESHOLD and coverage > T_COVERAGE_THRESHOLD and tmscore > T_TMSCORE_THRESHOLD:
        return 'T'
    else:
        if tmscore > T_TMSCORE_THRESHOLD:
            return 'N'
        else:
            return 'No_Hit'

def determine_code(target_id, hit_type):
    cath_code = target_id.split('__')[0]
    if hit_type == 'H':
        return cath_code
    else:
        cat_code = '.'.join(cath_code.split('.')[:3])
        return cat_code

def determine_best_hit(hits):
    h_hits = [hit for hit in hits if hit['type'] == 'H']
    t_hits = [hit for hit in hits if hit['type'] == 'T']
    n_hits = [hit for hit in hits if hit['type'] == 'N']
    no_hits = [hit for hit in hits if hit['type'] == 'No_Hit']

    h_hits.sort(key=lambda x: (x['evalue'], -x['tmscore']))
    t_hits.sort(key=lambda x: (-x['tmscore'], x['evalue']))

    if h_hits:
        return h_hits[0]
    elif t_hits:
        return t_hits[0]
    elif n_hits:
        n_hits.sort(key=lambda x: (-x['tmscore'], x['evalue']))
        return n_hits[0]
    elif no_hits:
        no_hits.sort(key=lambda x: (-x['tmscore'], x['evalue']))
        return no_hits[0]
    return None

def write_best_hit(outfile, query_id, best_hit):
    outfile.write(f"{query_id} {best_hit['code']} {best_hit['type']}\n")

if __name__ == '__main__':
    process_foldseek() 
