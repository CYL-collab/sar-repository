"""Generate a preview co-author network using librarian's canonicalization heuristics.

Outputs:
- assets/coauthor-preview.json : {nodes: [{id, name}], edges: [{source, target, weight}]}
- data/coauthor_mapping.csv : original_name, canonical_name, canonical_id

This script intentionally keeps canonicalization logic self-contained to avoid
import cycles or side-effects from importing Librarian (which may call DBLP).
"""
import csv
import json
import os
from collections import defaultdict, Counter

LIST_FILE = 'data/list.csv'
MAPPING_CSV = 'data/coauthor_mapping.csv'
OUT_JSON = 'assets/coauthor-preview.json'

# --- canonicalization helpers (copied/adapted from src/librarian.py) ---

def norm(name: str) -> str:
    return ' '.join(name.split()).strip()


def canonical_key(name: str):
    s = norm(name)
    if not s:
        return ('', (), ())
    s = s.replace('-', ' ')
    s_no_dots = s.replace('.', '')
    parts_check = [p.strip() for p in s.split(',') if p.strip()]
    suffixes = {'jr', 'jr.', 'ii', 'iii', 'iv'}
    if len(parts_check) >= 2 and parts_check[0].lower() in suffixes:
        rest = ','.join(parts_check[1:]).strip()
        s = rest + ' ' + parts_check[0]
        s_no_dots = s.replace('.', '')
    if ',' in s:
        parts = [p.strip() for p in s.split(',') if p.strip()]
        surname = parts[0]
        given = parts[1] if len(parts) > 1 else ''
    else:
        parts = s_no_dots.split()
        if len(parts) == 1:
            surname = parts[0]
            given = ''
        else:
            if parts[-1].lower() in suffixes and len(parts) >= 2:
                surname = parts[-2] + ' ' + parts[-1]
                given = ' '.join(parts[:-2])
            else:
                surname = parts[-1]
                given = ' '.join(parts[:-1])
            given = ' '.join(parts[:-1])
    given = given.strip()
    initials = []
    given_tokens = []
    if given:
        g = given.replace('.', '').strip()
        g_parts = [gp.replace(' ', '') for gp in g.split() if gp]
        for gp in g_parts:
            if len(gp) > 1 and gp.isalpha() and gp.upper() == gp and len(gp) <= 4:
                for ch in gp:
                    initials.append(ch.lower())
            elif len(gp) == 1 and gp.isalpha():
                initials.append(gp.lower())
            else:
                given_tokens.append(gp.lower())
                initials.append(gp[0].lower())
    return (surname.lower(), tuple(initials), tuple(given_tokens))


def initials_in_token(init_tuple, token):
    t = token.lower()
    pos = 0
    for ch in init_tuple:
        found = t.find(ch, pos)
        if found == -1:
            return False
        pos = found + 1
    return True


def is_same_name(n1: str, n2: str) -> bool:
    k1 = canonical_key(n1)
    k2 = canonical_key(n2)
    s1, init1, given1 = k1[0], k1[1], k1[2]
    s2, init2, given2 = k2[0], k2[1], k2[2]
    if not s1 or not s2:
        return False
    suffixes = {'jr', 'jr.', 'ii', 'iii', 'iv'}
    def base_surname(s):
        parts = s.split()
        if parts and parts[-1].lower() in suffixes:
            return ' '.join(parts[:-1])
        return s
    if base_surname(s1) != base_surname(s2):
        return False
    has_full1 = bool(given1)
    has_full2 = bool(given2)
    if (not init1 and not has_full1) and (not init2 and not has_full2):
        return True
    if has_full1 and has_full2:
        if given1[0] == given2[0] or given1[0].startswith(given2[0]) or given2[0].startswith(given1[0]):
            return True
        return False
    if init1 and init2:
        if init1 == init2:
            return True
        if len(init1) <= len(init2) and init2[:len(init1)] == init1:
            return True
        if len(init2) <= len(init1) and init1[:len(init2)] == init2:
            return True
    if has_full1 and init2:
        g1_initials = tuple(tok[0] for tok in given1 if tok)
        if len(init2) >= 2:
            if init2 == tuple(g1_initials[:len(init2)]) or initials_in_token(init2, given1[0]):
                return True
        else:
            if len(given1[0]) >= 6 and init2[0] == given1[0][0]:
                return True
    if has_full2 and init1:
        g2_initials = tuple(tok[0] for tok in given2 if tok)
        if len(init1) >= 2:
            if init1 == tuple(g2_initials[:len(init1)]) or initials_in_token(init1, given2[0]):
                return True
        else:
            if len(given2[0]) >= 6 and init1[0] == given2[0][0]:
                return True
    return False

# --- end canonicalization helpers ---


def split_authors(author_field: str):
    if not author_field:
        return []
    if ';' in author_field:
        parts = [p.strip() for p in author_field.split(';') if p.strip()]
    elif ' and ' in author_field:
        parts = [p.strip() for p in author_field.split(' and ') if p.strip()]
    else:
        parts = [author_field.strip()]
    return parts


def build_preview():
    if not os.path.exists(LIST_FILE):
        print(f"error: {LIST_FILE} not found")
        return

    # collect all raw author names
    papers = []
    with open(LIST_FILE, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            papers.append(r)

    raw_authors = []
    paper_author_lists = []  # list of lists for each paper
    for p in papers:
        authors_field = p.get('author', '') or ''
        names = split_authors(authors_field)
        clean_names = [norm(n) for n in names if norm(n)]
        paper_author_lists.append(clean_names)
        raw_authors.extend(clean_names)

    # build canonical groups: iterate through unique raw authors and cluster
    unique_raw = []
    seen = set()
    for a in raw_authors:
        k = a.lower()
        if k in seen:
            continue
        seen.add(k)
        unique_raw.append(a)

    # clustering
    clusters = []  # list of lists of raw names
    for name in unique_raw:
        placed = False
        for cl in clusters:
            if is_same_name(cl[0], name):
                cl.append(name)
                placed = True
                break
        if not placed:
            clusters.append([name])

    # choose canonical name for each cluster
    # Prefer variants that contain full given-name tokens (e.g. 'Xiaobai Sun')
    # over short/inverted forms like 'Sun, X.'; tie-break by length.
    canonical_map = {}
    canonical_list = []
    def has_full_given(nm):
        k = canonical_key(nm)
        # given_tokens (third element) indicates full given-name tokens
        return bool(k[2])

    for cid, cl in enumerate(clusters, start=1):
        best = cl[0]
        best_score = -10**9
        for nm in cl:
            score = len(nm)
            if has_full_given(nm):
                # strong preference for full given names
                score += 1000
            # penalize inverted comma-only forms if they lack full given tokens
            if (',' in nm) and (not has_full_given(nm)):
                score -= 300
            if score > best_score:
                best_score = score
                best = nm
        canonical_name = best
        canonical_list.append({'id': cid, 'name': canonical_name, 'members': cl})
        for nm in cl:
            canonical_map[nm] = (cid, canonical_name)

    # build nodes
    nodes = [{'id': c['id'], 'name': c['name'], 'size': len(c['members'])} for c in canonical_list]
    id_by_name = {c['name']: c['id'] for c in canonical_list}

    # build weighted edges (coauthorship counts)
    edge_counter = Counter()
    for authors in paper_author_lists:
        # map author raw name -> canonical id if known
        ids = []
        for a in authors:
            map_entry = canonical_map.get(a)
            if map_entry:
                ids.append(map_entry[0])
        # for each unordered pair
        ids = sorted(set(ids))
        for i in range(len(ids)):
            for j in range(i+1, len(ids)):
                edge_counter[(ids[i], ids[j])] += 1

    edges = [{'source': s, 'target': t, 'weight': w} for (s, t), w in edge_counter.items()]

    # ensure output directories exist
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(MAPPING_CSV), exist_ok=True)

    # write JSON
    out = {'nodes': nodes, 'edges': edges}
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # write mapping CSV
    with open(MAPPING_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['original_name', 'canonical_name', 'canonical_id'])
        for orig, (cid, cname) in sorted(canonical_map.items(), key=lambda x: (x[1][0], x[0])):
            writer.writerow([orig, cname, cid])

    # print summary
    print(f'preview written: {OUT_JSON} (nodes={len(nodes)}, edges={len(edges)})')
    top_edges = edge_counter.most_common(10)
    print('top edges (id,id,weight):')
    for (s,t),w in top_edges:
        name_s = next((n['name'] for n in nodes if n['id']==s), str(s))
        name_t = next((n['name'] for n in nodes if n['id']==t), str(t))
        print(f'  {s},{t} ({w}) \t {name_s} -- {name_t}')

if __name__ == '__main__':
    build_preview()
