import csv 

class Paper:
  def __init__(self, js) -> None:
    # normalize input dict keys to lower-case for resilience
    if isinstance(js, dict):
      lowered = {str(k).strip().lower(): v for k, v in js.items()}
    else:
      # fallback: try to convert object with attributes
      lowered = {}
    def get(*keys, default=''):
      for k in keys:
        if k in lowered and lowered[k] is not None:
          return lowered[k]
      return default

    self.year = get('year', default='')
    self.type = get('type', 'item type', default='')
    self.author = get('author', 'creators', default='')
    self.title = get('title', default='')
    self.field = get('field', 'language', default='')
    self.tag = get('tag', 'manual tags', 'automatic tags', default='')
    self.booktitle = get('booktitle', 'publication title', 'journal', default='')
    self.abbr = get('abbr', 'journal abbreviation', default='')
    self.vol = get('vol', 'volume', default='')
    self.no = get('no', 'number', 'issue', default='')
    self.pages = get('pages', default='')
    self.doi = get('doi', default='')
  
  def __str__(self) -> str:
    return "{}\n{}\n{}\n".format(self.author, self.title, self.venue_str())

  def venue_str(self) -> str:
    venue = self.booktitle
    if self.abbr != '':
      venue += ' ({})'.format(self.abbr)
    if self.type == 'inproceedings':
      venue += ', {}: {}'.format(self.year, self.pages)
    elif self.type == 'article':
      venue += ','
      if self.vol != '':
        venue += ' vol.{},'.format(self.vol)
      if self.no != '':
        venue += ' no.{},'.format(self.no)
      venue += ' pp.{}, {}'.format(self.pages, self.year)
    return venue

if __name__ == '__main__':
  # Try common encodings when reading CSV files to avoid UnicodeDecodeError
  csv_path = 'data/list.csv'
  data = []
  try:
    # Prefer UTF-8 with BOM handling
    with open(csv_path, 'r', encoding='utf-8-sig') as file:
      reader = csv.DictReader(file)
      data = list(reader)
  except UnicodeDecodeError:
    try:
      # Fallback to a common Windows encoding
      with open(csv_path, 'r', encoding='cp1252') as file:
        reader = csv.DictReader(file)
        data = list(reader)
    except UnicodeDecodeError:
      # As a last resort read with latin-1 and replace undecodable bytes so script continues
      with open(csv_path, 'r', encoding='latin-1', errors='replace') as file:
        reader = csv.DictReader(file)
        data = list(reader)

  # Normalize rows: map common CSV headers (Zotero export style) to the keys expected by Paper
  def normalize_row(row: dict) -> dict:
    # build lower-case lookup for original row
    lc = {k.strip().lower(): v for k, v in row.items()}

    def pick(*candidates):
      for c in candidates:
        if c in lc and lc[c] is not None:
          return lc[c]
      return ''

    normalized = {
      'year': pick('year'),
      'type': pick('item type', 'type'),
      'author': pick('author', 'creators'),
      'title': pick('title'),
      'field': pick('language', 'field'),
      'tag': pick('manual tags', 'automatic tags', 'tags'),
      'booktitle': pick('publication title', 'conference name', 'meeting name', 'journal'),
      'abbr': pick('journal abbreviation', 'journal abbreviation (iso)'),
      'vol': pick('volume', 'vol'),
      'no': pick('number', 'issue'),
      'pages': pick('pages'),
      'doi': pick('doi')
    }
    return normalized

  # Apply normalization
  data = [normalize_row(r) for r in data]

  if len(data) == 0:
    print('no data rows found in CSV')
  else:
    p = Paper(data[0])
    print(p)
