import argparse
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
import datetime


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class JobCache:
    def __init__(self, db_path="job_cache.db"):
        self.connection = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                title TEXT,
                company TEXT,
                location TEXT,
                date_posted TEXT,
                points INTEGER,
                matched_keywords TEXT,
                full_description TEXT,
                job_link TEXT,
                applied BOOLEAN DEFAULT 0,
                date_applied TEXT
            )
        """)
        self.connection.commit()

    def add_job(self, job_id, title, company, location, date_posted, points, matched_keywords, full_description, job_link):
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO jobs 
            (job_id, title, company, location, date_posted, points, matched_keywords, full_description, job_link)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (job_id, title, company, location, date_posted, points, matched_keywords, full_description, job_link))
        self.connection.commit()

    def update_job_as_applied(self, job_id):
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE jobs SET applied = 1, date_applied = ? WHERE job_id = ?
        """, (datetime.date.today().isoformat(), job_id))
        self.connection.commit()

    def query_jobs(self, query):
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def close(self):
        self.connection.close()


class LinkedInScraper:
    def __init__(self, driver, xpaths, filters, credentials):
        self.driver = driver
        self.xpaths = xpaths
        self.filters = filters
        self.credentials = credentials

    def login(self):
        self.driver.get("https://www.linkedin.com/login")
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, self.xpaths["login"]["username"])))
        self.driver.find_element(By.XPATH, self.xpaths["login"]["username"]).send_keys(self.credentials["email"])
        self.driver.find_element(By.XPATH, self.xpaths["login"]["password"]).send_keys(self.credentials["password"])
        self.driver.find_element(By.XPATH, self.xpaths["login"]["submit"]).click()
        time.sleep(5)

    def generate_search_url(self, filters):
        """
        Generates a LinkedIn job search URL based on filters.
        """
        base_url = "https://www.linkedin.com/jobs/search/?"
        params = []

        # Add keywords
        if "keywords" in filters:
            keywords = "%20AND%20".join(filters["keywords"])
            params.append(f"keywords={keywords}")

        # Add location
        if "location" in filters:
            params.append(f"location={filters['location'].replace(' ', '%20')}")

        # Add date posted filter
        if "date_posted" in filters:
            date_posted_map = {
                "past_24_hours": "r86400",
                "past_week": "r604800",
                "past_month": "r2592000"
            }
            date_posted_code = date_posted_map.get(filters["date_posted"], "")
            if date_posted_code:
                params.append(f"f_TPR={date_posted_code}")

        # Easy Apply filter
        if filters.get("easy_apply_only", False):
            params.append("f_AL=true")

        # Verified companies filter
        if filters.get("verification", False):
            params.append("f_C=ALL")

        # Salary range
        if "salary_range" in filters:
            salary = filters["salary_range"].replace("-", ",")
            params.append(f"f_SB2={salary}")

        # Job type filter
        if "job_type" in filters:
            job_types = {
                "Full-time": "F",
                "Part-time": "P",
                "Contract": "C",
                "Internship": "I",
                "Temporary": "T"
            }
            job_type_codes = ",".join([job_types[jt] for jt in filters["job_type"] if jt in job_types])
            params.append(f"f_JT={job_type_codes}")

        # Work mode filter
        if "work_mode" in filters:
            work_modes = {
                "Remote": "1",
                "Hybrid": "2",
                "Onsite": "3"
            }
            work_mode_codes = ",".join([work_modes[wm] for wm in filters["work_mode"] if wm in work_modes])
            params.append(f"f_WT={work_mode_codes}")

        # Experience level filter
        if "experience_level" in filters:
            experience_levels = {
                "Internship": "1",
                "Entry level": "2",
                "Associate": "3",
                "Mid-Senior level": "4",
                "Director": "5",
                "Executive": "6"
            }
            experience_codes = ",".join([experience_levels[el] for el in filters["experience_level"] if el in experience_levels])
            params.append(f"f_E={experience_codes}")

        return base_url + "&".join(params)
    
    def search_jobs(self):
        search_url = self.generate_search_url(self.filters)
        self.driver.get(search_url)
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
                points += 1

        # Check for negative words
        for word in negative_words:
            if word.lower() in full_description.lower():
                points -= 1

        return points
    
    def extract_job_details(self, filters, cache):
        total_jobs_text = self.driver.find_element(By.XPATH, self.xpaths["job_search"]["total_jobs"]).text
        total_pages = min(math.ceil(int(total_jobs_text.split()[0].replace(',', '')) / 25), 40)
        jobs_scanned = 0
        blacklisted_jobs = []
        skipped_jobs = []

        blacklisted_companies = filters.get("blacklisted_companies", [])

        print(f"{Colors.HEADER}Starting job scanning...{Colors.ENDC}")
        for page in range(total_pages):
            if jobs_scanned >= filters['max_jobs']:
                break

            page_offset = 25 * page
            self.driver.get(self.driver.current_url + f"&start={page_offset}")
            time.sleep(random.uniform(2, 5))

            try:
                job_cards = self.driver.find_elements(By.XPATH, self.xpaths["job_search"]["job_card"])

                for card in job_cards:

                    if jobs_scanned >= filters['max_jobs']:
                        print(f"{Colors.OKGREEN} Scanned {filters['max_jobs']} as mentioned in 'job_filters.yaml' {Colors.ENDC}")
                        break

                    job_id = card.get_attribute("data-occludable-job-id")
                    job_link = f"https://www.linkedin.com/jobs/view/{job_id}"

                                        # Skip previously viewed jobs   
                    if cache.query_jobs(f"SELECT 1 FROM jobs WHERE job_id = '{job_id}'"):
                        skipped_jobs.append(job_id)
                        continue

                    self.driver.execute_script("arguments[0].scrollIntoView(true);", card)
                    time.sleep(1)
                    card.click()
                    time.sleep(3)

                    title = self.driver.find_element(By.XPATH, self.xpaths["job_search"]["job_title"]).text
                    company = self.driver.find_element(By.XPATH, self.xpaths["job_search"]["company"]).text
                    primary_description = self.driver.find_element(By.XPATH, self.xpaths["job_search"]["primary_description"]).text
                    primary_dict = self.parse_primary_description(primary_description)

                    # Check for blacklisted companies
                    if company.lower() in [c.lower() for c in blacklisted_companies]:
                        print(f"{Colors.FAIL}Blacklisted job detected: {title} at {company}{Colors.ENDC}")
                        blacklisted_jobs.append({
                            "job_id": job_id,
                            "title": title,
                            "company": company,
                            "location": primary_dict["Location"],
                            "date_posted": primary_dict["Posting Date"]
                        })
                        self.driver.back()
                        time.sleep(2)
                        continue

                    try:
                        show_more_button = self.driver.find_element(By.XPATH, self.xpaths["job_search"]["show_more_button"])
                        self.driver.execute_script("arguments[0].click();", show_more_button)
                        time.sleep(2)
                    except:
                        pass

                    full_description_element = self.driver.find_element(By.XPATH, self.xpaths["job_search"]["full_description"])
                    full_description = " ".join([span.text for span in full_description_element.find_elements(By.TAG_NAME, "span")])

                    points = self.calculate_description_points(full_description, filters)
                    matched_keywords = [word for word in filters["description"]["positive"] if word.lower() in full_description.lower()]

                    cache.add_job(
                        job_id=job_id,
                        title=title,
                        company=company,
                        location=primary_dict["Location"],
                        date_posted=primary_dict["Posting Date"],
                        points=points,
                        matched_keywords=", ".join(matched_keywords),
                        full_description=full_description,
                        job_link=job_link
                    )

                    # Print formatted job details
                    print(f"{Colors.OKBLUE}--------------------------------------------------------------------------------------------{Colors.ENDC}")
                    print(f"{Colors.HEADER}Title: {title} | Company: {company} | Job ID: {job_id}{Colors.ENDC}")
                    print(f"{Colors.OKGREEN}Location: {primary_dict['Location']} | Date Posted: {primary_dict['Posting Date']}{Colors.ENDC}")
                    print(f"{Colors.OKCYAN}Matched Keywords: {matched_keywords}{Colors.ENDC}")
                    print(f"{Colors.OKBLUE}--------------------------------------------------------------------------------------------{Colors.ENDC}")

                    jobs_scanned += 1
                    self.driver.back()
                    time.sleep(2)

            except Exception as e:
                print(f"{Colors.WARNING}Error loading page: {e}{Colors.ENDC}")

        # Print summary of skipped and blacklisted jobs
        print(f"{Colors.HEADER}Job Scanning Complete{Colors.ENDC}")
        print(f"{Colors.OKCYAN}Total Jobs Scanned: {jobs_scanned}{Colors.ENDC}")
        print(f"{Colors.WARNING}Skipped Jobs (Previously Viewed): {len(skipped_jobs)}{Colors.ENDC}")
        # for job in skipped_jobs:
        #     print(f" - {Colors.FAIL}Job ID: {job}{Colors.ENDC}")

        print(f"{Colors.FAIL}Blacklisted Jobs: {len(blacklisted_jobs)}{Colors.ENDC}")
        for job in blacklisted_jobs:
            print(f" - {Colors.FAIL}{job['title']} at {job['company']} | Location: {job['location']} | Date Posted: {job['date_posted']}{Colors.ENDC}")


    def recommend_and_apply_jobs(self, cache, resume_config):
        """
        Recommends jobs based on ranking, suggests a resume, and handles application status.
        """
        jobs = cache.query_jobs("SELECT job_id, title, company, location, points, job_link, matched_keywords FROM jobs WHERE applied = 0 ORDER BY points DESC")
        applications_completed = 0
        for job in jobs:
            if applications_completed >= resume_config['applications']:
                print(f"Congratulations you applied for {applications_completed} jobs.")
                break
            job_id, title, company, location, points, job_link, matched_keywords = job
            matched_keywords_list = matched_keywords.split(", ") if matched_keywords else []

            # Recommend resume based on matched keywords
            suggested_resume = self.select_resume(matched_keywords_list, resume_config)

            print(f"{Colors.HEADER}Recommendation:{Colors.ENDC}")
            print(f"Title: {title}")
            print(f"Company: {company}")
            print(f"Location: {location}")
            print(f"Points: {points}")
            print(f"Link: {job_link}")
            print(f"Matched Keywords: {Colors.OKCYAN}{matched_keywords_list}{Colors.ENDC}")
            print(f"Suggested Resume: {Colors.OKGREEN}{suggested_resume}{Colors.ENDC}")

            # Prompt user input for application
            user_input = input(f"Did you apply for Job ID {job_id}? (yes/no): ").strip().lower()
            if user_input == "yes":
                print(f"Applying to Job ID {job_id}...")
                cache.update_job_as_applied(job_id)
                print(f"{Colors.OKGREEN}Marked Job ID {job_id} as applied.{Colors.ENDC}")
                applications_completed+=1
            else:
                print(f"{Colors.WARNING}Skipped Job ID {job_id}.{Colors.ENDC}")


    def select_resume(self, matched_keywords, resume_config):
        """
        Selects the best resume based on matched keywords.
        """
        best_resume = None
        max_matches = 0

        for resume, keywords in resume_config.items():
            matches = sum(1 for keyword in matched_keywords if keyword.lower() in map(str.lower, keywords))
            if matches > max_matches:
                best_resume = resume
                max_matches = matches

        return best_resume if best_resume else "default_resume.pdf"

    def generate_stats(self, cache):
        total_jobs = cache.query_jobs("SELECT COUNT(*) FROM jobs")[0][0]
        applied_jobs = cache.query_jobs("SELECT COUNT(*) FROM jobs WHERE applied = 1")[0][0]
        unique_companies = cache.query_jobs("SELECT COUNT(DISTINCT company) FROM jobs")[0][0]

        print(f"{Colors.HEADER}Job Statistics:{Colors.ENDC}")
        print(f"Total Jobs: {total_jobs}")
        print(f"Total Applications: {applied_jobs}")
        print(f"Unique Companies: {unique_companies}")
        


def main():
    parser = argparse.ArgumentParser(description="LinkedIn Job Automation Script")
    parser.add_argument("--mode", required=True, choices=["scan", "apply", "stats"], help="Select mode: scan, apply, or stats")
    args = parser.parse_args()

    with initialize(config_path="configs"):
        filters = compose(config_name="job_filters")
        credentials = compose(config_name="credentials")
        xpaths = compose(config_name="xpaths")
        resume = compose(config_name="resume")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    cache = JobCache()

    try:
        scraper = LinkedInScraper(driver, xpaths, filters, credentials)

        if args.mode == "scan":
            scraper.login()
            scraper.search_jobs()
            scraper.extract_job_details(filters, cache)
        elif args.mode == "apply":
            scraper.recommend_and_apply_jobs(cache, resume)
        elif args.mode == "stats":
            scraper.generate_stats(cache)

    except Exception as e:
        print(f"{Colors.FAIL}An error occurred: {e}{Colors.ENDC}")

    finally:
        cache.close()
        driver.quit()


if __name__ == "__main__":
    main()
