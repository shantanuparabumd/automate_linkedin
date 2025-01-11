# `scraper.py` - LinkedIn Job Scraper

The `scraper.py` script is responsible for interacting with LinkedIn's job search and managing the automation of job scraping, ranking, and recommendations. This script uses Selenium to automate the browser and scrape job-related data based on filters and configurations provided in YAML files.

---

## Features

### 1. **Login**
- Automates the LinkedIn login process using credentials from `credentials.yaml`.

### 2. **Generate Search Query**
- Dynamically generates a LinkedIn job search URL based on filters defined in `job_filters.yaml`.

### 3. **Scrape Job Details**
- Extracts job information such as title, company, location, date posted, and job description.
- Filters jobs based on keywords, including positive, negative, and priority (`best`) keywords.
- Saves job details to the database (`job_cache.db`).

### 4. **Recommend Jobs**
- Suggests jobs to apply for based on rankings derived from keyword matches and job posting dates.
- Recommends the best resume to use for each job based on overlapping keywords.

### 5. **Generate Statistics**
- Displays statistics about jobs in the database, including:
  - Total jobs
  - Applied jobs
  - Unique companies

---

## Workflow

### **Login**
The `login` function logs into LinkedIn using the credentials provided in `credentials.yaml`.

```python
def login(self):
    self.driver.get("https://www.linkedin.com/login")
    WebDriverWait(self.driver, 10).until(
        EC.presence_of_element_located((By.XPATH, self.xpaths["login"]["username"]))
    )
    self.driver.find_element(By.XPATH, self.xpaths["login"]["username"]).send_keys(
        self.credentials["email"]
    )
    self.driver.find_element(By.XPATH, self.xpaths["login"]["password"]).send_keys(
        self.credentials["password"]
    )
    self.driver.find_element(By.XPATH, self.xpaths["login"]["submit"]).click()
    time.sleep(15)
```

---

### **Generate Search Query**
The `generate_search_url` function dynamically constructs a LinkedIn job search URL using the filters specified in `job_filters.yaml`.

Supported filters:
- Keywords
- Location
- Date Posted
- Job Type (e.g., Full-time, Contract)
- Work Mode (e.g., Remote, Hybrid, Onsite)
- Experience Level (e.g., Entry-level, Mid-Senior)
- Salary Range

```python
def generate_search_url(self, filters):
    base_url = "https://www.linkedin.com/jobs/search/?"
    params = []

    if "keywords" in filters:
        keywords = "%20AND%20".join(filters["keywords"])
        params.append(f"keywords={keywords}")

    if "location" in filters:
        params.append(f"location={filters['location'].replace(' ', '%20')}")

    if "date_posted" in filters:
        date_posted_map = {
            "past_24_hours": "r86400",
            "past_week": "r604800",
            "past_month": "r2592000",
        }
        params.append(f"f_TPR={date_posted_map.get(filters['date_posted'], '')}")

    # Additional filters...
    return base_url + "&".join(params)
```

---

### **Scrape Job Details**
The `extract_job_details` function iterates through the job search results, scraping relevant job data. It:
1. Skips jobs already in the database.
2. Filters out jobs from blacklisted companies.
3. Evaluates job descriptions against positive, negative, and priority keywords.
4. Saves relevant jobs to the database.

```python
def extract_job_details(self, filters, cache):
    job_cards = self.driver.find_elements(
        By.XPATH, self.xpaths["job_search"]["job_card"]
    )

    for card in job_cards:
        job_id = card.get_attribute("data-occludable-job-id")
        job_link = f"https://www.linkedin.com/jobs/view/{job_id}"

        # Skip previously viewed jobs
        if cache.query_jobs(f"SELECT 1 FROM jobs WHERE job_id = '{job_id}'"):
            continue

        # Scrape job details
        title = self.driver.find_element(By.XPATH, self.xpaths["job_search"]["job_title"]).text
        company = self.driver.find_element(By.XPATH, self.xpaths["job_search"]["company"]).text
        # Filter and save relevant jobs
```

---

### **Recommend Jobs**
The `recommend_and_apply_jobs` function suggests jobs to apply for based on:
1. Keyword matches in job descriptions.
2. Scores calculated for each job.
3. Recommended resumes based on overlapping keywords.

```python
def recommend_and_apply_jobs(self, cache, resume_config):
    jobs = cache.query_jobs(
        "SELECT job_id, title, company, location, points, job_link, matched_keywords FROM jobs WHERE applied = 0 ORDER BY points DESC"
    )
    for job in jobs:
        # Suggest the best resume based on matched keywords
        suggested_resume = self.select_resume(matched_keywords_list, resumes)
        print(f"Suggested Resume: {Colors.OKGREEN}{suggested_resume}{Colors.ENDC}")
```

---

### **Statistics**
The `generate_stats` function provides an overview of the database contents:
- Total jobs
- Applied jobs
- Unique companies

```python
def generate_stats(self, cache):
    total_jobs = cache.query_jobs("SELECT COUNT(*) FROM jobs")[0][0]
    applied_jobs = cache.query_jobs("SELECT COUNT(*) FROM jobs WHERE applied = 1")[0][0]
    unique_companies = cache.query_jobs("SELECT COUNT(DISTINCT company) FROM jobs")[0][0]

    print(f"Total Jobs: {total_jobs}")
    print(f"Applied Jobs: {applied_jobs}")
    print(f"Unique Companies: {unique_companies}")
```

---

## Usage

### **Run Modes**
- **`scan` mode**: Scrapes jobs based on filters and saves relevant jobs to the database.
- **`apply` mode**: Recommends jobs to apply for and suggests the best resume for each job.
- **`stats` mode**: Displays statistics about the job database.

---

## Notes
- This script relies on the following YAML configuration files:
  - `credentials.yaml`: For LinkedIn login credentials.
  - `job_filters.yaml`: For filtering job search results.
  - `xpaths.yaml`: For specifying HTML element locators used by Selenium.
  - `resume.yaml`: For mapping resumes to keywords.
- Always ensure these files are correctly configured before running the script.

For more details, refer to the [Main README](../README.md).
