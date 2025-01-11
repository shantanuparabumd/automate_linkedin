
# LinkedIn Job Automation

This project automates LinkedIn job search and application processes using Python. It scrapes job data, ranks jobs based on keywords, and suggests which resume to use for tailored applications. The database allows easy tracking of applied and pending jobs.

---

## Table of Contents
- [Setup](#setup)
- [Usage](#usage)
  - [Modes in `automate.py`](#modes-in-automatepy)
  - [Database Analysis with `database.py`](#database-analysis-with-databasepy)
- [Configuration Files](#configuration-files)
  - [Credentials](#credentialsyaml)
  - [Job Filters](#job_filtersyaml)
  - [Resumes](#resumeyaml)
  - [XPaths](#xpathsyaml)
- [Code Structure](#code-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Setup

Follow these steps to set up the project:

1. **Install Miniconda**  
   Download and install [Miniconda](https://docs.anaconda.com/miniconda/install/#quick-command-line-install) for your platform.

2. **Clone the Repository**  
   ```bash
   git clone https://github.com/your-repo/linkedin-job-automation.git
   cd linkedin-job-automation
   ```

3. **Create and Activate Virtual Environment**  
   ```bash
   conda create -n linkedin-automation python=3.10 -y
   conda activate linkedin-automation
   ```

4. **Install Dependencies**  
   Install dependencies using one of the following methods:
   - **From `requirements.txt`:**
     ```bash
     pip install -r requirements.txt
     ```
   - **Directly from `setup.py`:**
     ```bash
     pip install -e .
     ```

5. **Ensure WebDriver is Installed**  
   The script uses Chrome WebDriver. Ensure you have Chrome installed and let `webdriver_manager` manage the WebDriver.

---

## Usage

### Modes in `automate.py`

Run the main automation script in one of the three modes:

1. **Scan Mode**  
   ```bash
   python automate.py --mode scan
   ```
   - Logs into LinkedIn using credentials from `credentials.yaml`.
   - Uses `xpaths.yaml` to locate HTML elements.
   - Searches jobs using filters from `job_filters.yaml`.
   - Ranks jobs based on keywords and stores them in a database.

2. **Apply Mode**  
   ```bash
   python automate.py --mode apply
   ```
   - Suggests jobs to apply for based on ranking.
   - Recommends which resume to use (based on `resume.yaml`).
   - Tracks applied jobs and skips them in future runs.

3. **Stats Mode**  
   ```bash
   python automate.py --mode stats
   ```
   - Displays job statistics:
     - Total jobs
     - Applied jobs
     - Unique companies

---

### Database Analysis with `database.py`

Use `database.py` to analyze the database and export job data to CSV.

1. **Analyze Database**  
   ```bash
   python database.py
   ```
   - Highlights jobs older than 25 days.
   - Increases the ranking of jobs close to expiration.

2. **Export to CSV**  
   When prompted, choose to export the database to a CSV file.  
   The CSV includes essential details for easy viewing in Excel or Google Sheets.

[See More Details](./docs/database.md)

---

## Configuration Files

### `credentials.yaml`
Stores your LinkedIn login details:
```yaml
email: your_email@example.com
password: your_password
```

### `job_filters.yaml`
Defines filters for job searches:
- **Keywords**: Targeted job roles.
- **Location**: Geographic preference.
- **Job Type**: Full-time, contract, etc.
- **Work Mode**: Remote, hybrid, onsite.
- **Experience Level**: Entry-level, mid-senior, etc.
- **Positive/Negative Keywords**: Prioritizes or skips jobs.

[See Full Example](./docs/job_filters.md)

### `resume.yaml`
Defines resumes and associated keywords:
```yaml
resumes:
  Python_Resume.pdf:
    - "Python"
    - "Machine Learning"
    - "AI"
    - "Data Science"
applications: 3
```

### `xpaths.yaml`
Specifies LinkedIn HTML elements for scraping:
```yaml
login:
  username: "//input[@id='username']"
  password: "//input[@id='password']"
  submit: "//button[@type='submit']"
```
[See Full Example](./docs/xpaths.md)

---

## Code Structure

- **`automate.py`**: Main script to scan, apply, or show stats.
- **`database.py`**: Analyze and export the job database.
- **`job_cache.py`**: Database management.
- **`scraper.py`**: LinkedIn scraping logic. [See More Details](./docs/scraper.md)

- **`utils.py`**: Utility functions and styling.
- **`configs/`**: YAML configuration files.

---

## Contributing

We welcome contributions! Follow these steps:
1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature
   ```
3. Submit a pull request with detailed information.

### Issue Template
[See Issue Template](./.github/ISSUE_TEMPLATE.md)

### Pull Request Template
[See PR Template](./.github/PULL_REQUEST_TEMPLATE.md)

---

