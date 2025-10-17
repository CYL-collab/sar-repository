"""
This script is used to manage the data files.
* Search new papers from DBLP and add them into an add.csv file (need further manual process)
* Update scholar.csv based on the current list.csv file 
"""
import csv
import os
from dblp import DBLP

class Librarian:
  def __init__(self):
    self.dblp = DBLP()

    self.paper_list_filename = 'data/list.csv'
    self.paper_list_fields = ['year', 'type', 'author', 'title', 'field', 'tag', 
                              'booktitle', 'abbr', 'vol', 'no', 'pages', 'doi']  
    
    self.scholar_filename = 'data/scholar.csv'
    self.scholar_fields = ['id', 'name', 'institution', 'category', 'country', 'homepage']
    # Ensure scholar file exists with proper header. If missing, create it.
    if not os.path.exists(self.scholar_filename):
      os.makedirs(os.path.dirname(self.scholar_filename), exist_ok=True)
      with open(self.scholar_filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=self.scholar_fields)
        writer.writeheader()
      print('[librarian] created "{}" with headers'.format(self.scholar_filename))

    # get the list of current papers
    with open(self.paper_list_filename, 'r', encoding='utf-8') as file:
      reader = csv.DictReader(file)
      self.papers = list(reader)
    print('[librarian] load {} papers from "{}"'.format(len(self.papers), self.paper_list_filename))
    # get the list of current scholars
    with open(self.scholar_filename, 'r', encoding='utf-8') as file:
      reader = csv.DictReader(file)
      self.scholar = list(reader)
    print('[librarian] load {} scholars from "{}"'.format(len(self.scholar), self.scholar_filename))
  
  def search_new_papers(self, keywords, year=None, output_file='data/add.csv'):
    """
    Search DBLP and write new papers found into a file. Note that this often contain papers 
    that are irrelevant to CIT.
    """
    # these paper titles are already included in repository
    paper_titles = [e['title'].lower() for e in self.papers]

    # these paper titles should be excluded
    with open('data/excluded/excluded_format.txt', 'r', encoding='utf-8') as file:
      excluded_titles = [e.strip().lower() for e in file.readlines()]
    with open('data/excluded/excluded_irrelevant.txt', 'r', encoding='utf-8') as file:
      excluded_titles += [e.strip().lower() for e in file.readlines()]

    # search dblp for new papers
    new_papers = self.dblp.search_paper(keywords=keywords,
                                        already_have=paper_titles, 
                                        excluded=excluded_titles,
                                        after_year=year)
    
    # write the new papers into the add.csv file
    with open(output_file, 'w', encoding='utf-8') as file:
      writer = csv.DictWriter(file, fieldnames=self.paper_list_fields)
      writer.writeheader()
      for each in new_papers:
        writer.writerow(each)

    print('[librarian] write {} papers to "{}" (might be irrelevant to CIT)'.format(len(new_papers), output_file))

  def update_scholar(self):
    """
    Update scholar.csv accoridng to list.csv
    """
    # read current names and build normalized lookup
    current_names = [e.get('name', '').strip() for e in self.scholar]
    current_norm = {n.lower() for n in current_names if n}

    paper_names = []
    raw_new = []

    def split_authors(author_field: str):
      """Split an author field into individual author strings.
      Prefer semicolon as separator; fall back to ' and ' or single value.
      """
      if not author_field:
        return []
      # Many Zotero exports use ';' between authors and comma inside names
      if ';' in author_field:
        parts = [p.strip() for p in author_field.split(';') if p.strip()]
      elif ' and ' in author_field:
        parts = [p.strip() for p in author_field.split(' and ') if p.strip()]
      else:
        # if no semicolon and no ' and ', assume the whole field is one author
        parts = [author_field.strip()]
      return parts

    # Basic name normalization: strip and lower. Also provide a helper to
    # compare potential abbreviation vs full-name (simple heuristic).
    def norm(name: str) -> str:
      return ' '.join(name.split()).strip()

    def canonical_key(name: str) -> tuple:
      """Return a canonical representation for a name string.
      We'll return (surname, initials_list, given_tokens) where:
      - surname: lowercase surname string
      - initials_list: tuple of lower-case initial letters extracted from given names (may be empty)
      - given_tokens: tuple of full given-name tokens (lowercase) when available

      This richer key lets us match 'Trivedi, K.', 'Trivedi, K. S.', 'Trivedi, Kishor',
      and 'Kishor S Trivedi' more reliably by comparing surname and initials/given tokens.
      """
      s = norm(name)
      if not s:
        return ('', (), ())
      # normalize hyphens and multiple spaces
      s = s.replace('-', ' ')
      s_no_dots = s.replace('.', '')
      # handle inverted suffix like 'Jr., Rivalino Matias' -> move Jr to surname side
      parts_check = [p.strip() for p in s.split(',') if p.strip()]
      # detect suffix-only first token like 'Jr' or 'Jr.' or roman numerals
      suffixes = {'jr', 'jr.', 'ii', 'iii', 'iv'}
      if len(parts_check) >= 2 and parts_check[0].lower() in suffixes:
        # treat as surname suffix attached to surname of the rest
        # e.g., 'Jr., Rivalino Matias' -> name becomes 'Rivalino Matias Jr'
        rest = ','.join(parts_check[1:]).strip()
        s = rest + ' ' + parts_check[0]
        s_no_dots = s.replace('.', '')
      # Decide surname and given part
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
          # handle possible suffix at end (e.g., 'Matias Jr')
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
        # normalize 'Kaiyuan' vs 'Kai-Yuan' differences by removing spaces in tokens when appropriate
        g_parts = [gp.replace(' ', '') for gp in g.split() if gp]
        for gp in g_parts:
          # GP might be concatenated initials like 'KS' or a normal name like 'Kishor'
          if len(gp) > 1 and gp.isalpha() and gp.upper() == gp and len(gp) <= 4:
            # treat as sequence of initials
            for ch in gp:
              initials.append(ch.lower())
          elif len(gp) == 1 and gp.isalpha():
            initials.append(gp.lower())
          else:
            # treat as full token; record token and its initial
            given_tokens.append(gp.lower())
            initials.append(gp[0].lower())

      return (surname.lower(), tuple(initials), tuple(given_tokens))

    def is_same_name(n1: str, n2: str) -> bool:
      k1 = canonical_key(n1)
      k2 = canonical_key(n2)
      s1, init1, given1 = k1[0], k1[1], k1[2]
      s2, init2, given2 = k2[0], k2[1], k2[2]
      if not s1 or not s2:
        return False
      # surnames must match (compare base surname without suffixes like jr, ii)
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

      # both have only surname
      if (not init1 and not has_full1) and (not init2 and not has_full2):
        return True

      # If both are full names (no initials), match only on explicit equality or close prefix
      if has_full1 and has_full2:
        if given1[0] == given2[0] or given1[0].startswith(given2[0]) or given2[0].startswith(given1[0]):
          return True
        return False

      # If both have initials, allow exact or prefix match (K vs K S -> prefix)
      if init1 and init2:
        if init1 == init2:
          return True
        if len(init1) <= len(init2) and init2[:len(init1)] == init1:
          return True
        if len(init2) <= len(init1) and init1[:len(init2)] == init2:
          return True

      # Now one side is initials and the other has full given tokens.
      # For initials vs full-name: if initials length >=2, require they match corresponding initials
      # If initials length ==1, only match when the full given token is long (>=6) to avoid Yan/Yun type collisions
      def initials_in_token(init_tuple, token):
        # check whether initials appear in order inside token (e.g., 'k','y' in 'kaiyuan')
        t = token.lower()
        pos = 0
        for ch in init_tuple:
          found = t.find(ch, pos)
          if found == -1:
            return False
          pos = found + 1
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

    # --- deduplicate existing scholars by clustering similar names ---
    def dedupe_existing_scholars():
      # Build clusters of indices where names are considered the same
      clusters = []
      for idx, s in enumerate(self.scholar):
        name = s.get('name', '').strip()
        if not name:
          clusters.append({'rep': idx, 'members': [idx]})
          continue
        placed = False
        for cl in clusters:
          rep_name = self.scholar[cl['rep']].get('name', '')
          if is_same_name(rep_name, name):
            cl['members'].append(idx)
            placed = True
            break
        if not placed:
          clusters.append({'rep': idx, 'members': [idx]})

      # Identify clusters with >1 member
      multi = [cl for cl in clusters if len(cl['members']) > 1]
      if not multi:
        return None

      merged_summary = []
      new_scholars = []
      # For each cluster, pick a representative and merge other records into it
      for cl in clusters:
        members = cl['members']
        if len(members) == 1:
          new_scholars.append(self.scholar[members[0]])
          continue

        # Choose representative:
        # 1) prefer an entry that looks like 'Surname, Given' (contains a comma and surname first)
        # 2) otherwise prefer longest name (more complete)
        best_idx = members[0]
        best_score = -1
        for mi in members:
          nm = (self.scholar[mi].get('name') or '')
          score = 0
          if ',' in nm:
            # prefer comma-formatted names
            score += 1000
          score += len(nm)
          # smaller id as slight tiebreaker
          try:
            score -= int(self.scholar[mi].get('id', 0) or 0) * 0.0001
          except Exception:
            pass
          if score > best_score:
            best_score = score
            best_idx = mi

        rep = dict(self.scholar[best_idx])
        removed_info = []  # list of (id, name)
        for mi in members:
          if mi == best_idx:
            continue
          other = self.scholar[mi]
          removed_info.append((other.get('id', ''), other.get('name', '')))
          # merge non-empty fields if rep lacks them
          for f in self.scholar_fields:
            if f in ('id', 'name'):
              continue
            if not rep.get(f):
              val = other.get(f, '')
              if val:
                rep[f] = val

        new_scholars.append(rep)
        merged_summary.append((rep.get('id', ''), removed_info, rep.get('name', '')))

      # Backup and write merged scholars back to file
      try:
        import shutil
        bak_name = self.scholar_filename + '.bak'
        shutil.copy(self.scholar_filename, bak_name)
      except Exception:
        bak_name = None

      # sort new_scholars by surname then name to group same-family entries together
      def scholar_sort_key(rec):
        name = (rec.get('name') or '')
        sk = canonical_key(name)
        return (sk[0] or '', name)

      new_scholars_sorted = sorted(new_scholars, key=scholar_sort_key)

      with open(self.scholar_filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=self.scholar_fields)
        writer.writeheader()
        for r in new_scholars_sorted:
          writer.writerow({k: r.get(k, '') for k in self.scholar_fields})

      # Update in-memory list
      self.scholar = new_scholars
      return {'backup': bak_name, 'merged': merged_summary}

    # Run dedupe now (merge duplicates in existing scholar.csv)
    dedupe_result = dedupe_existing_scholars()
    if dedupe_result:
      print('[librarian] deduplicated scholar.csv; backup: {}'.format(dedupe_result.get('backup')))
      for rep_id, removed_info, rep_name in dedupe_result.get('merged'):
        # removed_info is list of (id, name)
        removed_str = ', '.join([f"{rid}:{rname}" for rid, rname in removed_info]) if removed_info else ''
        print(f"\tkept id {rep_id} ({rep_name}), removed: {removed_str}")

    # Collect paper author names and raw candidates for new names
    for each in self.papers:
      authors_field = each.get('author', '') or ''
      names = split_authors(authors_field)
      for name in names:
        name = name.strip()
        if not name:
          continue
        paper_names.append(name)
        # compare normalized against existing names (and consider heuristics)
        n_norm = norm(name)
        matched = False
        if n_norm in current_norm:
          matched = True
        else:
          # try fuzzy check against existing names
          for ex in current_names:
            if is_same_name(ex, name):
              matched = True
              break
        if not matched:
          raw_new.append(name)

    # Deduplicate new names while preserving order, using normalized key
    seen = set()
    new_names = []
    for n in raw_new:
      key = norm(n)
      if key in seen:
        continue
      # also ensure it doesn't match current_names by heuristic
      already = False
      for ex in current_names:
        if is_same_name(ex, n):
          already = True
          break
      if already:
        continue
      seen.add(key)
      new_names.append(n)

    print('[librarian] found {} new scholar names ({} unique)'.format(len(raw_new), len(new_names)))

    # Print names from scholar that do not appear in papers
    for each in current_names:
      if each not in paper_names:
        print('\tnot appear in paper list: ' + each)

    if len(new_names) > 0:
      # determine next id: try to find max existing id if present
      max_id = 0
      for s in self.scholar:
        try:
          sid = int(s.get('id', 0) or 0)
          if sid > max_id:
            max_id = sid
        except Exception:
          continue
      next_id = max_id + 1 if max_id >= 1 else len(current_names) + 1

      # append new unique names with incremental ids
      # Instead of appending unsorted, add new entries to in-memory list then sort and rewrite file
      for name in new_names:
        self.scholar.append({'id': str(next_id), 'name': name, 'institution': '', 'category': '', 'country': '', 'homepage': ''})
        next_id += 1

      # Write full sorted scholar list back
      def scholar_sort_key(rec):
        name = (rec.get('name') or '')
        sk = canonical_key(name)
        return (sk[0] or '', name)

      scholars_sorted = sorted(self.scholar, key=scholar_sort_key)
      with open(self.scholar_filename, 'w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=self.scholar_fields)
        writer.writeheader()
        for r in scholars_sorted:
          writer.writerow({k: r.get(k, '') for k in self.scholar_fields})
      print('[librarian] successfully wrote {} new scholars'.format(len(new_names)))

  def check_paper_inclusion(self, filename, start=None, end=None):
    """
    Determine whether the papers (titles) listed in the file are included in DBLP.
    Each line in the file should be in the format of "index, title"
    """
    with open(filename, encoding='utf-8') as file:
      lines = file.readlines()

    for row, each in enumerate(lines):
      if (start is not None and row < start - 1) or (end is not None and row > end - 1):
        continue

      paper_title = each[each.find(',') + 1:].strip().lower()
      result, _ = self.dblp.check_paper(paper_title)
      if result == 'no_match':
        print('[{}] {}'.format(result, paper_title))

if __name__ == '__main__':
  lib = Librarian()
  # lib.search_new_papers(keywords=['software aging', 'software rejuvenation'])
  lib.update_scholar()
