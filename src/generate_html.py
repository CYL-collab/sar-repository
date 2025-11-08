import csv
import pandas as pd
from bs4 import BeautifulSoup
from papers import Paper

class Generator:
  def __init__(self, sort=False):
    self.list_filename = 'data/list.csv'
    self.scholar_filename = 'data/scholar.csv'

    # sort csv and get statistic data 
    self.data = self.read_csv(sort) 

    # read all papers from the csv file
    self.papers = []
    with open(self.list_filename, 'r', encoding='utf-8') as file:
      for each in csv.DictReader(file):
        p = Paper(each)
        self.papers.append(p)
    
    # read all scholars from the csv file
    self.scholars = []
    with open(self.scholar_filename, 'r', encoding='utf-8') as file:
      for each in csv.DictReader(file):
        self.scholars.append(each)
    
    print('[INFO] read {} papers from "{}"'.format(len(self.papers), self.list_filename))
    print('       read {} scholars from "{}"'.format(len(self.scholars), self.scholar_filename))


  def read_csv(self, sort) -> dict:
    """
    Read csv file and calculate statistics for the basic BAR and PIE charts.
    """
    # Read CSV with common encoding fallbacks and normalize column names
    try:
      df = pd.read_csv(self.list_filename, sep=',', header=0, encoding='utf-8-sig')
    except Exception:
      try:
        df = pd.read_csv(self.list_filename, sep=',', header=0, encoding='cp1252')
      except Exception:
        df = pd.read_csv(self.list_filename, sep=',', header=0, encoding='latin-1', engine='python')

    # Normalize column names to lower-case and trim
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Map common header names to canonical names expected by the script
    col_map = {}
    if 'publication title' in df.columns:
      col_map['publication title'] = 'booktitle'
    if 'journal' in df.columns and 'booktitle' not in df.columns:
      col_map['journal'] = 'booktitle'
    # apply mapping
    if col_map:
      df = df.rename(columns=col_map)

    # Ensure key columns exist
    if 'year' in df.columns:
      df['year'] = pd.to_numeric(df['year'], errors='coerce').fillna(0).astype(int)
    else:
      # missing year column -> create default
      df['year'] = 0

    if 'booktitle' not in df.columns:
      df['booktitle'] = ''
    if 'title' not in df.columns:
      df['title'] = ''

    # Now safe to sort
    df = df.sort_values(['year', 'booktitle', 'title'], ascending=False)
    
    # cumulative number of publications
    bar_data = df.groupby('year').size().to_frame('number')
    bar_data['cumulative'] = bar_data['number'].cumsum()
    print(bar_data)

    # distribution of topics - dynamic classification based on repo_analysis_tags
    field_counts = {
      'Model-based Analysis': 0,
      'Measurement-based Analysis': 0,
      'Hybrid Analysis': 0,
      'Indicator': 0,
      'Rejuvenation': 0,
      'ARB Prediction': 0,
      # 'Classification': 0,
      'Testing': 0,
      'Other Mitigation': 0,
      'Other': 0
    }
    
    # Process each row and classify based on repo_analysis_tags
    if 'repo_analysis_tags' in df.columns:
      for tags_str in df['repo_analysis_tags'].fillna(''):
        tags_lower = str(tags_str).lower()
        
        # Track which categories this row matches (can match multiple)
        matched = False
        
        # Classification rules (in order of priority)
        if '度量' in tags_lower:
          field_counts['Indicator'] += 1
          matched = True
        elif 'model' in tags_lower:
          field_counts['Model-based Analysis'] += 1
          matched = True
        elif 'measurement' in tags_lower:
          field_counts['Measurement-based Analysis'] += 1
          matched = True
        elif 'hybrid' in tags_lower:
          field_counts['Hybrid Analysis'] += 1
          matched = True
        elif 'arb prediction' in tags_lower or 'arb' in tags_lower:
          field_counts['ARB Prediction'] += 1
          matched = True
        elif 'rej' in tags_lower:
          field_counts['Rejuvenation'] += 1
          matched = True
        elif 'testing' in tags_lower:
          field_counts['Testing'] += 1
          matched = True
        elif 'other' in tags_lower:
          field_counts['Other Mitigation'] += 1
          matched = True
        
        # If no specific match found, classify as 'Other'
        if not matched:
          field_counts['Other'] += 1
    else:
      # If repo_analysis_tags column doesn't exist, default to 'Other'
      field_counts['Other'] = len(df)
    
    # Convert to DataFrame and sort by count
    pie_data = pd.DataFrame(list(field_counts.items()), columns=['field', 'count'])
    pie_data = pie_data.sort_values('count', ascending=False)

    # final data
    data = {}
    year = bar_data.index.values.tolist()
    number = bar_data['number'].values.tolist()
    cumulative = bar_data['cumulative'].values.tolist()
    # find index for year 2000 (or first year >= 2000). If not present, start from 0
    try:
      index = year.index(2000)
    except ValueError:
      index = 0
      for i, y in enumerate(year):
        try:
          if int(y) >= 2000:
            index = i
            break
        except Exception:
          continue
    data['year'] = year[index:]
    data['number'] = number[index:]
    data['cumulative'] = cumulative[index:]
    data['fields'] = pie_data['field'].values.tolist()
    data['count'] = pie_data['count'].values.tolist()

    if sort:
      df.to_csv(self.list_filename, sep=',', encoding='utf-8', index=False, header=True)

    return data

  def generate_index(self, date):
    """
    Generate the static index.html file. Need to reaplce the followings:
    * Description of the sub-title <- last update date
    * Statistics <- number of papers, [TODO: scholars, institutions]
    * Bar chart <- cumulative number of publications (with date)
    * Pie chart <- distribution of research topics
    """
    # read the template HTML file 
    with open('pages/_index.html', 'r') as file:
      text = file.read()

    soup = BeautifulSoup(text, 'html.parser')

    # insert reusable sidebar fragment if available
    try:
      with open('components/_sidebar.html', 'r', encoding='utf-8') as sf:
        sidebar_html = sf.read()
      # replace existing sidebar region
      sidebar_start = soup.find(string=lambda text: isinstance(text, str) and '<!-- Sidebar' in text)
      # safer replacement: find the comment nodes
      # remove current sidebar block if present by locating the first div.sidebar
      old_sidebar = soup.find('div', class_='sidebar')
      if old_sidebar:
        new_sidebar = BeautifulSoup(sidebar_html, 'html.parser')
        old_sidebar.replace_with(new_sidebar)
    except Exception:
      # ignore if sidebar fragment missing
      pass

    # description and statistics
    element = soup.find(id='replace-description')
    element.string = 'Collection of Research Papers of Software Aging'.format(date)

    element = soup.find(id='replace-number-1')
    element.string = '{}'.format(len(self.papers))

    element = soup.find(id='replace-number-2')
    element.string = '{}'.format(len(self.scholars))

    element = soup.find(id='replace-bar-descrption')
    element.string = 'From 1995 to {}'.format(date.split()[-1])
  
    # chart data
    with open('assets/index-chart.js','r') as f:
      lines = f.readlines()
    
    # bar chart
    lines[6] = '    labels: [{}],\n'.format(', '.join(['"{}"'.format(e) for e in self.data['year']]))
    lines[12] = '        data: {}\n'.format(str(self.data['cumulative']))
    # pie chart
    lines[46] = '        data: {},\n'.format(str(self.data['count']))
    lines[50] = '    labels: [{}]\n'.format(', '.join(['"{}"'.format(e) for e in self.data['fields']]))

    with open('assets/index-chart.js', 'w') as f:
      for line in lines:
        f.write(line)

    # write the new HTML
    with open('index.html', 'w') as file:
      file.write(str(soup))
    print('[INFO] succesfully update list.html"')


  def generate_list(self):
    """
    Generate the static components/list.html file. Need to reaplce the followings:
    * Description of the sub-title <- number of papers
    * Data table <- complete paper list
    """
    # read the template HTML file 
    with open('pages/_list.html', 'r') as file:
      text = file.read()

    soup = BeautifulSoup(text, 'html.parser')

    # insert reusable sidebar fragment if available
    try:
      with open('components/_sidebar.html', 'r', encoding='utf-8') as sf:
        sidebar_html = sf.read()
      old_sidebar = soup.find('div', class_='sidebar')
      if old_sidebar:
        new_sidebar = BeautifulSoup(sidebar_html, 'html.parser')
        old_sidebar.replace_with(new_sidebar)
    except Exception:
      pass

    # Post-process sidebar for components/list.html context: fix hrefs and active class
    try:
      # home link should point to ../index.html from components/
      home_a = soup.find('i', class_='fas fa-home')
      if home_a and home_a.parent and home_a.parent.name == 'a':
        home_link = home_a.parent
        home_link['href'] = '../index.html'
      # set All Papers as active and its link to '#'
      all_papers_icon = soup.find('i', class_='fas fa-layer-group')
      if all_papers_icon and all_papers_icon.parent and all_papers_icon.parent.name == 'a':
        all_a = all_papers_icon.parent
        # In components context, All Papers should point to the local list.html
        all_a['href'] = 'list.html'
        # ensure the parent li has active class and remove 'active' from other li siblings
        li = all_a.find_parent('li')
        if li:
          # remove 'active' from sibling li elements to avoid multiple active items
          parent_ul = li.find_parent('ul')
          if parent_ul:
            for sib in parent_ul.find_all('li', recursive=False):
              classes = sib.get('class', [])
              if 'active' in classes:
                classes = [c for c in classes if c != 'active']
                sib['class'] = classes
          # now set active on the All Papers li
          li['class'] = li.get('class', [])
          if 'active' not in li['class']:
            li['class'].append('active')
      # coauthor link should be relative inside components folder
      co_a_icon = soup.find('i', class_='fas fa-file')
      if co_a_icon and co_a_icon.parent and co_a_icon.parent.name == 'a':
        co_a = co_a_icon.parent
        co_a['href'] = 'coauthor.html'
    except Exception:
      pass

    # replace "XX papers included"
    element = soup.find(id='replace-description')
    element.string = '{} papers included'.format(len(self.papers))

    # replace data table 
    element = soup.find(id='replace-paper-data-tbody')
    element.string = ''
    # print(element)

    # create a new row for each item in data
    # and add this new row into the HTML table
    for each in self.papers:
      new_row = soup.new_tag('tr')
      name_cell = BeautifulSoup('<td>{}</td>'.format(each.year), 'html.parser')
      age_cell = BeautifulSoup(
        '<td><p>{}<br><strong>{}</strong><br><em>{}</em></p></td>'.format(
          each.author, each.title, each.venue_str()), 'html.parser')
      doi_cell = BeautifulSoup(
        '<td><a href="https://www.doi.org/{}" target="_blank">DOI</a></td>'.format(
          each.doi), 'html.parser')

      new_row.append(name_cell)
      new_row.append(age_cell)
      new_row.append(doi_cell)
      element.append(new_row)
      # print(element)

    # write the new HTML
    with open('components/list.html', 'w', encoding='utf-8') as file:
      file.write(str(soup))
    print('[INFO] succesfully add {} rows into "components/list.html"'.format(len(self.papers)))

  def generate_coauthor(self):
    """
    Generate the static components/coauthor.html from pages/_coauthor.html template.
    """
    with open('pages/_coauthor.html', 'r', encoding='utf-8') as file:
      text = file.read()

    soup = BeautifulSoup(text, 'html.parser')

    # insert sidebar fragment
    try:
      with open('components/_sidebar.html', 'r', encoding='utf-8') as sf:
        sidebar_html = sf.read()
      old_sidebar = soup.find('div', class_='sidebar')
      if old_sidebar:
        new_sidebar = BeautifulSoup(sidebar_html, 'html.parser')
        old_sidebar.replace_with(new_sidebar)
    except Exception:
      pass

    # fix links for components context
    try:
      # Home -> ../index.html
      home_a = soup.find('i', class_='fas fa-home')
      if home_a and home_a.parent and home_a.parent.name == 'a':
        home_a.parent['href'] = '../index.html'
      # All Papers -> list.html
      all_a_icon = soup.find('i', class_='fas fa-layer-group')
      if all_a_icon and all_a_icon.parent and all_a_icon.parent.name == 'a':
        all_a_icon.parent['href'] = 'list.html'
        # ensure the parent li for All Papers is not accidentally left inactive/active incorrectly
        all_li = all_a_icon.parent.find_parent('li')
        if all_li:
          all_li['class'] = all_li.get('class', [])
          # remove active from all siblings first
          for sib in all_li.find_parent('ul').find_all('li', recursive=False):
            classes = sib.get('class', [])
            if 'active' in classes:
              classes = [c for c in classes if c != 'active']
              sib['class'] = classes
        
      # Co-author -> coauthor.html (self)
      co_a_icon = soup.find('i', class_='fas fa-file')
      if co_a_icon and co_a_icon.parent and co_a_icon.parent.name == 'a':
        co_a_icon.parent['href'] = 'coauthor.html'
        # mark Co-author li as active
        co_li = co_a_icon.parent.find_parent('li')
        if co_li:
          co_li['class'] = co_li.get('class', [])
          if 'active' not in co_li['class']:
            co_li['class'].append('active')
    except Exception:
      pass

    # write out the generated components/coauthor.html
    # To avoid any duplicated top-level documents (in case template contains multiple),
    # write only the first <html> element and prefix with DOCTYPE.
    first_html = soup.find('html')
    out_text = ''
    if first_html:
      out_text = '<!DOCTYPE html>\n' + str(first_html)
    else:
      out_text = str(soup)
    with open('components/coauthor.html', 'w', encoding='utf-8') as f:
      f.write(out_text)
    print('[INFO] succesfully generated components/coauthor.html')

if __name__ == '__main__':
  g = Generator(sort=True)
  g.generate_index(date='Nov 2024')
  g.generate_list()
  g.generate_coauthor()
