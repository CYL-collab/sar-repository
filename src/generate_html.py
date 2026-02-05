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
      'Understanding (UND)': 0,
      'Measurement (MEA)': 0,
      'Testing (TES)': 0,
      'Aging process analysis (ANA)': 0,
      'Rejuvenation (REJ)': 0,
      'Prediction (PRE)': 0,
      'Other Mitigation Methods (OTM)': 0,
      'Other': 0
    }
    
    # Process each row and classify based on repo_analysis_tags
    if 'repo_analysis_tags' in df.columns:
      for tags_str in df['repo_analysis_tags'].fillna(''):
        category_name, _ = self._classify_tags_internal(tags_str)
        if category_name in field_counts:
          field_counts[category_name] += 1
        else:
          field_counts['Other'] += 1
          print(f'[DEBUG] Unclassified tags: "{tags_str}"')
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

  def _classify_tags_internal(self, tags_str):
    """
    Internal method to classify tags based on repo_analysis_tags content.
    Returns tuple: (category_name, css_class)
    """
    if not tags_str or str(tags_str).strip() == '':
      return 'Other', 'other'
    
    tags_lower = str(tags_str).lower()
    
    # Classification rules (in order of priority)
    if '度量' in tags_lower or ('mea' in tags_lower and 'measurement' not in tags_lower):
      return 'Measurement (MEA)', 'measurement'
    elif 'model' in tags_lower:
      return 'Aging process analysis (ANA)', 'analysis'
    elif 'measurement' in tags_lower:
      return 'Aging process analysis (ANA)', 'analysis'
    elif 'hybrid' in tags_lower:
      return 'Aging process analysis (ANA)', 'analysis'
    elif 'arb prediction' in tags_lower or 'arb' in tags_lower or 'pre' in tags_lower:
      return 'Prediction (PRE)', 'prediction'
    elif 'rej' in tags_lower:
      return 'Rejuvenation (REJ)', 'rejuvenation'
    elif 'testing' in tags_lower or 'tes' in tags_lower:
      return 'Testing (TES)', 'testing'
    elif 'other' in tags_lower or '其他' in tags_lower:
      return 'Other Mitigation Methods (OTM)', 'other-mitigation'
    elif 'classification' in tags_lower or '分析bug报告' in tags_lower or '逻辑分析' in tags_lower or 'udn' in tags_lower:
      return 'Understanding (UND)', 'understanding'
    elif '现象分析' in tags_lower:
      return 'Understanding (UND)', 'understanding'
    print(f'[DEBUG] Unclassified tags: "{tags_lower}"')
    return 'Other', 'other'

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


  def classify_tag(self, tags_str):
    """
    Classify a paper based on its repo_analysis_tags using the same logic as index page pie chart
    """
    return self._classify_tags_internal(tags_str)

  def generate_list(self):
    """
    Generate the static components/list.html file. Need to reaplce the followings:
    * Description of the sub-title <- number of papers
    * Data table <- complete paper list
    * Add tag classification and filtering functionality
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
    
    # Update filter counts in the template
    filtered_count_element = soup.find(id='filteredCount')
    if filtered_count_element:
      filtered_count_element.string = str(len(self.papers))

    # replace data table 
    element = soup.find(id='replace-paper-data-tbody')
    element.string = ''
    
    # collect all years for the year filter
    years = sorted(list(set([paper.year for paper in self.papers])), reverse=True)
    
    # create a new row for each item in data
    # and add this new row into the HTML table
    for each in self.papers:
      # Get classification tag for this paper
      tag_display, tag_class = self.classify_tag(getattr(each, 'repo_analysis_tags', ''))
      
      # Define tag colors based on category
      tag_colors = {
        'measurement': 'badge-primary',
        'analysis': 'badge-info', 
        'prediction': 'badge-warning',
        'rejuvenation': 'badge-success',
        'testing': 'badge-danger',
        'other-mitigation': 'badge-secondary',
        'understanding': 'badge-und',
        'other': 'badge-light'
      }
      tag_color = tag_colors.get(tag_class, 'badge-light')
      
      new_row = soup.new_tag('tr')
      new_row['data-tag'] = tag_class
      new_row['data-year'] = str(each.year)
      
      year_cell = BeautifulSoup('<td>{}</td>'.format(each.year), 'html.parser')
      
      # Enhanced publication cell with tag badge
      # choose readable text color: dark text on light badges, white text otherwise
      text_color = 'text-dark' if tag_color == 'badge-light' else 'text-white'
      pub_cell_html = '''
      <td>
        <div class="mb-2">
          <span class="badge {} {}">{}</span>
        </div>
        <p>{}<br/><strong>{}</strong><br/><em>{}</em></p>
      </td>
      '''.format(tag_color, text_color, tag_display, each.author, each.title, each.venue_str())
      pub_cell = BeautifulSoup(pub_cell_html, 'html.parser')
      
      doi_cell = BeautifulSoup(
        '<td><a href="https://www.doi.org/{}" target="_blank">DOI</a></td>'.format(
          each.doi), 'html.parser')

      new_row.append(year_cell)
      new_row.append(pub_cell)
      new_row.append(doi_cell)
      element.append(new_row)

    # Add JavaScript for filtering functionality - replace existing DataTable initialization
    filter_script = '''
      $(document).ready(function () {
        // Store all rows data for filtering
        var allRowsData = [];
        var years = {};
        
        // Collect all data and years
        $('#basic-datatables tbody tr').each(function() {
          var $row = $(this);
          var rowData = {
            element: $row.clone(),
            tag: $row.data('tag'),
            year: $row.data('year'),
            text: $row.text().toLowerCase()
          };
          allRowsData.push(rowData);
          
          var year = $row.data('year');
          if (year) years[year] = true;
        });
        
        // Populate year filter
        var sortedYears = Object.keys(years).sort((a, b) => b - a);
        sortedYears.forEach(function(year) {
          $('#yearFilter').append('<option value="' + year + '">' + year + '</option>');
        });
        
        // Filter function - operates on all data
        function applyFilters() {
          var tagFilter = $('#tagFilter').val();
          var yearFilter = $('#yearFilter').val();
          var searchTerm = $('#searchInput').val().toLowerCase();
          var showAllResults = $('#showAllResults').val() === 'all';
          
          // Filter and re-populate table (build list first)
          var filteredData = [];
          allRowsData.forEach(function(rowData) {
            var show = true;
            
            // Tag filter
            if (tagFilter && rowData.tag !== tagFilter) {
              show = false;
            }
            
            // Year filter
            if (yearFilter && rowData.year.toString() !== yearFilter) {
              show = false;
            }
            
            // Search filter
            if (searchTerm && !rowData.text.includes(searchTerm)) {
              show = false;
            }
            
            if (show) {
              filteredData.push(rowData);
            }
          });
          
          // Update result counts
          $('#filteredCount').text(filteredData.length);
          if (filteredData.length !== allRowsData.length) {
            $('#totalCount').show().html(' (out of ' + allRowsData.length + ' total)');
          } else {
            $('#totalCount').hide();
          }

          // Destroy existing DataTable first to avoid restoring original rows
          if ($.fn.DataTable.isDataTable('#basic-datatables')) {
            $('#basic-datatables').DataTable().destroy();
          }

          // Clear tbody and append filtered rows
          $('#basic-datatables tbody').empty();
          filteredData.forEach(function(rowData) {
            $('#basic-datatables tbody').append(rowData.element.clone());
          });
          
          // Configure DataTable based on display option
          var dataTableConfig = {
            order: [[0, 'desc']],
            rowReorder: true,
            columnDefs: [
              { orderable: true, className: 'reorder', targets: 0 },
              { orderable: false, targets: '_all' }
            ],
            searching: false,
            info: true
          };
          
          if (showAllResults) {
            // Show all results without pagination
            dataTableConfig.paging = false;
            dataTableConfig.language = {
              info: 'Showing all _TOTAL_ entries'
            };
          } else {
            // Show with pagination
            dataTableConfig.pageLength = 25;
            dataTableConfig.paging = true;
            dataTableConfig.language = {
              info: 'Showing _START_ to _END_ of _TOTAL_ entries'
            };
          }
          
          // Reinitialize DataTable
          $("#basic-datatables").DataTable(dataTableConfig);
        }
        
        // Bind filter events
        $('#tagFilter, #yearFilter, #showAllResults').change(applyFilters);
        $('#searchInput').on('input', applyFilters);
        
        // Initialize DataTable with custom settings
        $("#basic-datatables").DataTable({
          pageLength: 25,
          order: [[0, 'desc']],
          rowReorder: true,
          columnDefs: [
            { orderable: true, className: 'reorder', targets: 0 },
            { orderable: false, targets: '_all' }
          ],
          // Disable default search since we have custom filters
          searching: false
        });
     });
    '''
    
    # Replace the existing script section instead of adding a new one
    existing_script = soup.find('script', string=lambda text: text and 'basic-datatables' in text and 'DataTable' in text)
    if existing_script:
      existing_script.string = filter_script
    
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
