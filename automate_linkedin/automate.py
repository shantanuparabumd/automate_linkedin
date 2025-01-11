import argparse
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from hydra import initialize, compose

from automate_linkedin.cache import JobCache
from automate_linkedin.scraper import LinkedInScraper
from automate_linkedin.utils import Colors

"""
LinkedIn Job Automation Script
================================

This script automates job searching, ranking, and suggestion processes on LinkedIn. It supports three modes: `scan`, `apply`, and `stats`.

USAGE:
------
Run the script with one of the three modes:
- `scan`: Scrapes LinkedIn jobs based on filters and stores them in a database.
- `apply`: Suggests jobs to apply for based on rankings and recommends a resume.
- `stats`: Displays statistics of the jobs in the database.

CONFIGURATION FILES:
--------------------
1. `credentials.yaml`: Contains LinkedIn login credentials.
2. `xpaths.yaml`: Stores XPaths for LinkedIn UI elements. This allows quick updates if LinkedIn's UI changes.
3. `job_filters.yaml`: Contains filters for job search, such as keywords, experience levels, and locations.
4. `resume.yaml`: Maps keywords to resumes and defines the number of applications to suggest in `apply` mode.

MODES EXPLAINED:
----------------
1. **Scan Mode**:
   - Logs in to LinkedIn using the credentials from `credentials.yaml`.
   - Uses the XPaths defined in `xpaths.yaml` to locate HTML elements for scraping.
   - Generates a job search query based on filters in `job_filters.yaml` (e.g., keywords, time, experience).
   - Scrapes job details such as title, company, posting date, location, and link.
   - Ranks jobs based on positive keywords in the description and skips irrelevant jobs with negative keywords.
   - Skips jobs already viewed using their unique job ID.
   - Saves relevant jobs to the database (`job_cache.db`) with details like:
     - Title, company, date of posting, location, and link.

2. **Apply Mode**:
   - Suggests jobs to apply for based on ranking and posting date.
   - Recommends the most suitable resume from `resume.yaml` based on overlapping keywords.
   - Allows the user to mark a job as applied or skip it:
     - If "applied", the job is marked in the database and won't be suggested again.
     - If "no", the job remains in the database and may be suggested in future runs.
   - Continues suggesting jobs until the user has applied to the number of jobs specified in `resume.yaml`.

3. **Stats Mode**:
   - Displays statistics about the jobs in the database, including:
     - Total jobs scraped.
     - Number of jobs applied to.
     - Number of unique companies.

"""

def main():
    parser = argparse.ArgumentParser(description="LinkedIn Job Automation Script")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["scan", "apply", "stats"],
        help="Select mode: scan, apply, or stats",
    )
    args = parser.parse_args()

    # Load configuration files
    with initialize(config_path="configs"):
        filters = compose(config_name="job_filters")
        credentials = compose(config_name="credentials")
        xpaths = compose(config_name="xpaths")
        resume = compose(config_name="resume")

    # Initialize database
    cache = JobCache()

    if args.mode == "scan":
        """
        SCAN MODE:
        ----------
        - Logs into LinkedIn using credentials from `credentials.yaml`.
        - Generates a job search query based on `job_filters.yaml`.
        - Scrapes jobs using the XPaths from `xpaths.yaml`.
        - Filters jobs based on description keywords.
        - Saves relevant jobs to the database.
        """
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        try:
            scraper = LinkedInScraper(driver, xpaths, filters, credentials)
            scraper.login()
            scraper.search_jobs()
            scraper.extract_job_details(filters, cache)
        except Exception as e:
            print(f"{Colors.FAIL}An error occurred during scan: {e}{Colors.ENDC}")
        finally:
            driver.quit()

    elif args.mode == "apply":
        """
        APPLY MODE:
        -----------
        - Suggests jobs from the database based on ranking and posting date.
        - Recommends the best resume for each job based on `resume.yaml`.
        - Asks the user whether they applied to a job:
          - "Yes": Marks the job as applied in the database.
          - "No": Keeps the job in the database for future suggestions.
        - Stops after suggesting the number of jobs specified in `resume.yaml`.
        """
        try:
            scraper = LinkedInScraper(
                None, xpaths, filters, credentials
            )  # Pass None as driver is not needed
            scraper.recommend_and_apply_jobs(cache, resume)
        except Exception as e:
            print(f"{Colors.FAIL}An error occurred during apply: {e}{Colors.ENDC}")

    elif args.mode == "stats":
        """
        STATS MODE:
        -----------
        - Displays statistics about the jobs in the database:
          - Total jobs.
          - Number of jobs applied to.
          - Number of unique companies.
        """
        try:
            scraper = LinkedInScraper(
                None, xpaths, filters, credentials
            )  # Pass None as driver is not needed
            scraper.generate_stats(cache)
        except Exception as e:
            print(f"{Colors.FAIL}An error occurred during stats: {e}{Colors.ENDC}")

    # Close the database connection
    cache.close()


if __name__ == "__main__":
    main()
