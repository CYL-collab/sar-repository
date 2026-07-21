# Software Aging Repository

The Software Aging Repository (SAR) is a curated, browsable collection of research on software aging and software rejuvenation. It combines structured publication and scholar data with a statically generated website that provides summary statistics, topic filtering, full-text metadata search, and an interactive co-authorship network.

The repository is designed to be easy to audit and reuse: CSV files are the source of truth, Python scripts perform maintenance and generation, and the published site requires no application server.

## Features

- Curated publication metadata covering software-aging and software-rejuvenation research.
- Searchable paper table with year and research-topic filters.
- Data-driven dashboard with publication, scholar, venue, timeline, and topic statistics.
- Interactive weighted co-authorship network with author search and edge filtering.
- DBLP-assisted discovery of candidate papers and scholar-name maintenance.
- Scheduled synchronization of the paper list from the SAR systematic-literature-review replication package.

## Repository structure

```text
.
|-- data/                 Source CSV files, exclusions, mappings, and archives
|-- pages/                HTML and JavaScript templates
|-- components/           Generated paper-list and co-author pages
|-- assets/               Styles, frontend dependencies, and generated chart/network data
|-- src/                  Data-management and static-site generation scripts
|-- .github/workflows/    Scheduled data synchronization
|-- index.html            Generated repository dashboard
`-- requirements.txt      Python dependencies
```

The primary data files are:

- `data/list.csv`: publication metadata and repository-specific classification tags;
- `data/scholar.csv`: scholar names, institutions, categories, countries, and homepages;
- `data/add.csv`: manually reviewed staging area for newly discovered papers;
- `data/coauthor_mapping.csv`: generated mapping from observed author names to canonical identities.

Generated files should not be edited by hand. Update the source data or templates and rebuild them instead.

## Requirements

- Python 3.9 or later
- The packages listed in `requirements.txt`

Create a virtual environment and install the dependencies:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS or Linux:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Build the website

Run generation commands from the repository root:

```bash
python src/generate_coauthor_preview.py
python src/generate_html.py
```

The first command rebuilds the canonical author mapping and co-authorship graph. The second rebuilds the dashboard, paper list, co-author page, and chart data. Counts, publication-year ranges, and chart values are calculated from the current CSV files; no update date or year range needs to be supplied manually.

The venue count is the number of distinct, non-empty `repo_venue_tags` values in `data/list.csv`. These curated labels avoid counting spelling and capitalization variants in publication titles as different venues.

To preview the site locally, serve the repository root with any static HTTP server, for example:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000/`. An HTTP server is recommended because browsers may block the co-author page from loading its JSON file directly from a `file://` URL.

## Maintain the data

`src/librarian.py` contains the main maintenance workflows. Its default entry point updates `data/scholar.csv` from the paper list:

```bash
python src/librarian.py
```

Candidate-paper discovery uses DBLP and writes results to `data/add.csv`. Candidates must be manually checked for relevance and metadata quality before being merged into `data/list.csv`. Excluded titles are maintained under `data/excluded/`.

See `src/README.md` for details about each script.

## Automated synchronization

`.github/workflows/sync-list.yml` periodically downloads `data/list.csv` from the [SAR SLR replication package](https://github.com/CYL-collab/SLR-of-SAR-Replication-Package). The workflow validates the file and its header before committing changes.

The synchronization workflow updates the source paper list only. After a data update, regenerate the static website and co-author assets so that the published counts and visualizations remain consistent with the CSV data.

## Data and generated-page model

```text
SLR replication package / DBLP / manual review
                     |
                     v
       data/list.csv + data/scholar.csv
                     |
          Python generation scripts
                     |
                     v
 index.html + components/*.html + assets/*.js/json
```

## License

This repository is released under the [CC0 1.0 Universal](LICENSE) public-domain dedication. See `LICENSE` for the complete terms.
