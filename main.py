import yaml
import math
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from hydra import initialize, compose
import sqlite3


class Colors:
    HEADER = '\033[95m'    # Light Purple
    OKBLUE = '\033[94m'    # Light Blue
    OKCYAN = '\033[96m'    # Cyan
    OKGREEN = '\033[92m'   # Green
    WARNING = '\033[93m'   # Yellow
    FAIL = '\033[91m'      # Red
    ENDC = '\033[0m'       # Reset to default
    BOLD = '\033[1m'       # Bold text
    UNDERLINE = '\033[4m'  # Underlined text

class JobCache:
    def __init__(self, db_path="job_cache.db"):
        self.connection = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_jobs (
                job_id TEXT PRIMARY KEY
            )
        """)
        self.connection.commit()

    def is_job_processed(self, job_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT 1 FROM processed_jobs WHERE job_id = ?", (job_id,))
        return cursor.fetchone() is not None

    def add_job(self, job_id):
        cursor = self.connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO processed_jobs (job_id) VALUES (?)", (job_id,))
        self.connection.commit()

    def close(self):
        self.connection.close()

class LinkedInScraper:
    def __init__(self, driver, xpaths, filters, credentials):
        self.driver = driver
        self.xpaths = xpaths
        self.filters = filters
        self.credentials = credentials

    def login(self):
        """Logs into LinkedIn using credentials."""
        self.driver.get("https://www.linkedin.com/login")
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self.xpaths["login"]["username"])))
        self.driver.find_element(By.XPATH, self.xpaths["login"]["username"]).send_keys(self.credentials["email"])
        self.driver.find_element(By.XPATH, self.xpaths["login"]["password"]).send_keys(self.credentials["password"])
        self.driver.find_element(By.XPATH, self.xpaths["login"]["submit"]).click()
        time.sleep(2)

    def search_jobs(self):
        """Navigates to the LinkedIn job search page using filters."""
        keywords = "%20AND%20".join(self.filters["keywords"])
        self.driver.get(f"https://www.linkedin.com/jobs/search/?keywords={keywords}")
        time.sleep(2)

    def parse_primary_description(self, description):
        """Parses the primary job description into location, posting date, and status."""
        parts = [part.strip() for part in description.split('·')]
        return {
            "Location": parts[0] if len(parts) > 0 else None,
            "Posting Date": parts[1] if len(parts) > 1 else None,
            "Status": parts[2] if len(parts) > 2 else None
        }


    def calculate_description_points(self, full_description, filters):
        """
        Calculate points for the job description based on the presence of positive and negative words.
        """
        positive_words = filters["description"]["positive"]
        negative_words = filters["description"]["negative"]
        points = 0

        # Check for positive words
        for word in positive_words:
            if word.lower() in full_description.lower():
                print(f"Found {Colors.OKGREEN} {word.lower()} {Colors.ENDC}")
                points += 1

        # Check for negative words
        for word in negative_words:
            if word.lower() in full_description.lower():
                print(f"Found {Colors.FAIL} {word.lower()} {Colors.ENDC}")
                points -= 1

        return points

    def extract_job_details(self, filters, cache):
        """Extracts job details for each job card."""
        job_data = []
        total_jobs_text = self.driver.find_element(By.XPATH, self.xpaths["job_search"]["total_jobs"]).text
        total_pages = min(math.ceil(int(total_jobs_text.split()[0].replace(',', '')) / 25), 40)

        loading_page = False

        for page in range(total_pages):
            if len(job_data) >= self.filters["max_jobs"]:
                break

            # Navigate through pages
            page_offset = 25 * page
            self.driver.get(self.driver.current_url + f"&start={page_offset}")
            time.sleep(random.uniform(2, 5))

            job_cards = self.driver.find_elements(By.XPATH, self.xpaths["job_search"]["job_card"])

            for card in job_cards:
                if len(job_data) >= self.filters["max_jobs"]:
                    break

                try:    

                    job_id = card.get_attribute("data-occludable-job-id")
                    print("Job ID: ",job_id)
                    loading_page = False

                    # Check if job is already processed
                    if cache.is_job_processed(job_id):
                        print(f"{Colors.FAIL} Skipping cached job ID: {job_id} {Colors.ENDC}")
                        continue

                    self.driver.execute_script("arguments[0].scrollIntoView(true);", card)
                    time.sleep(1)
                    card.click()
                    time.sleep(3)

                    # Extract details
                    title = self.driver.find_element(By.XPATH, self.xpaths["job_search"]["job_title"]).text
                    company = self.driver.find_element(By.XPATH, self.xpaths["job_search"]["company"]).text
                    primary_description = self.driver.find_element(By.XPATH, self.xpaths["job_search"]["primary_description"]).text
                    primary_dict = self.parse_primary_description(primary_description)

                    # Expand "Show More" section if available
                    try:
                        show_more_button = self.driver.find_element(By.XPATH, self.xpaths["job_search"]["show_more_button"])
                        self.driver.execute_script("arguments[0].click();", show_more_button)
                        time.sleep(2)
                    except:
                        pass

                    full_description_element = self.driver.find_element(By.XPATH, self.xpaths["job_search"]["full_description"])
                    full_description = " ".join([span.text for span in full_description_element.find_elements(By.TAG_NAME, "span")])

                    # Calculate points based on the description
                    points = self.calculate_description_points(full_description, filters)
                    print(f"Points for {Colors.OKGREEN}'{title}' {Colors.ENDC} at {Colors.OKBLUE}'{company}'{Colors.ENDC}: {points}")

                    # Append job data
                    job_data.append({
                        "Title": title,
                        "Company": company,
                        "Location": primary_dict["Location"],
                        "Posting Date": primary_dict["Posting Date"],
                        "Status": primary_dict["Status"],
                    })

                    # Add the job ID to cache
                    cache.add_job(job_id)
                    print(f"{Colors.OKCYAN} Adding {job_id} : {title} - {company} to viewed {Colors.ENDC}")

                    # Navigate back to job list
                    self.driver.back()
                    time.sleep(2)

                except Exception as e:
                    if loading_page==False:
                        print(f"{Colors.WARNING} Loading page ... {Colors.ENDC}")
                    loading_page = True

        return job_data


def main():
    with initialize(config_path="configs"):
        filters = compose(config_name="job_filters")
        credentials = compose(config_name="credentials")
        xpaths = compose(config_name="xpaths")

    # Setup WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    cache = JobCache()  # Initialize the cache

    try:
        scraper = LinkedInScraper(driver, xpaths, filters, credentials)
        scraper.login()
        scraper.search_jobs()
        job_details = scraper.extract_job_details(filters, cache)

        # Save to CSV
        df = pd.DataFrame(job_details)
        df.to_csv("linkedin_full_jobs.csv", index=False)
        print("Job data successfully saved to linkedin_full_jobs.csv")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
