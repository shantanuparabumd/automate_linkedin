import math
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from automate_linkedin.utils import Colors
from datetime import datetime, timedelta


class LinkedInScraper:
    """
    LinkedInScraper class handles the job of logging into LinkedIn, searching for jobs,
    filtering jobs based on user-defined criteria, and suggesting jobs for application.
    """

    def __init__(self, driver, xpaths, filters, credentials):
        """
        Initializes the LinkedInScraper class with the necessary dependencies.
        :param driver: Selenium WebDriver instance.
        :param xpaths: Dictionary containing XPaths for interacting with the LinkedIn site.
        :param filters: Dictionary containing filters for job search and ranking.
        :param credentials: Dictionary containing login credentials for LinkedIn.
        """
        self.driver = driver
        self.xpaths = xpaths
        self.filters = filters
        self.credentials = credentials

    def login(self):
        """
        Logs into LinkedIn using credentials provided in the YAML file.
        Navigates to the login page, enters credentials, and submits the form.
        """
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
        time.sleep(15)  # Wait for login to complete

    def generate_search_url(self, filters):
        """
        Generates a LinkedIn job search URL based on user-defined filters.
        :param filters: Dictionary containing filters such as keywords, location, etc.
        :return: Constructed URL as a string.
        """
        base_url = "https://www.linkedin.com/jobs/search/?"
        params = []

        # Add job keywords
        if "keywords" in filters:
            keywords = "%20AND%20".join(filters["keywords"])
            params.append(f"keywords={keywords}")

        # Add location filter
        if "location" in filters:
            params.append(f"location={filters['location'].replace(' ', '%20')}")

        # Add date posted filter
        if "date_posted" in filters:
            date_posted_map = {
                "past_24_hours": "r86400",
                "past_week": "r604800",
                "past_month": "r2592000",
            }
            date_posted_code = date_posted_map.get(filters["date_posted"], "")
            if date_posted_code:
                params.append(f"f_TPR={date_posted_code}")

        # Add Easy Apply filter
        if filters.get("easy_apply_only", False):
            params.append("f_AL=true")

        # Add filters for verified companies
        if filters.get("verification", False):
            params.append("f_C=ALL")

        # Add salary range filter
        if "salary_range" in filters:
            salary = filters["salary_range"].replace("-", ",")
            params.append(f"f_SB2={salary}")

        # Add job type filter
        if "job_type" in filters:
            job_types = {
                "Full-time": "F",
                "Part-time": "P",
                "Contract": "C",
                "Internship": "I",
                "Temporary": "T",
            }
            job_type_codes = ",".join(
                [job_types[jt] for jt in filters["job_type"] if jt in job_types]
            )
            params.append(f"f_JT={job_type_codes}")

        # Add work mode filter
        if "work_mode" in filters:
            work_modes = {"Remote": "1", "Hybrid": "2", "Onsite": "3"}
            work_mode_codes = ",".join(
                [work_modes[wm] for wm in filters["work_mode"] if wm in work_modes]
            )
            params.append(f"f_WT={work_mode_codes}")

        # Add experience level filter
        if "experience_level" in filters:
            experience_levels = {
                "Internship": "1",
                "Entry level": "2",
                "Associate": "3",
                "Mid-Senior level": "4",
                "Director": "5",
                "Executive": "6",
            }
            experience_codes = ",".join(
                [
                    experience_levels[el]
                    for el in filters["experience_level"]
                    if el in experience_levels
                ]
            )
            params.append(f"f_E={experience_codes}")

        return base_url + "&".join(params)

    def search_jobs(self):
        """
        Navigates to LinkedIn's job search page using the URL generated by filters.
        """
        search_url = self.generate_search_url(self.filters)
        self.driver.get(search_url)
        time.sleep(2)  # Allow time for the page to load

    def parse_relative_time(self, relative_time):
        """
        Converts a relative time string (e.g., '7 hours ago') into a datetime object.
        :param relative_time: String indicating how long ago the job was posted.
        :return: datetime object or None if parsing fails.
        """
        try:
            if not relative_time:
                return None

            # Handle cases like "Reposted 5 hours ago"
            if relative_time.startswith("Reposted"):
                relative_time = relative_time.replace("Reposted", "").strip()

            # Extract numeric value and time unit
            parts = relative_time.split()
            if len(parts) >= 2:
                value = int(parts[0])
                unit = parts[1].lower()

                # Convert relative time to a timedelta
                if "minute" in unit:
                    return datetime.now() - timedelta(minutes=value)
                elif "hour" in unit:
                    return datetime.now() - timedelta(hours=value)
                elif "day" in unit:
                    return datetime.now() - timedelta(days=value)
                elif "week" in unit:
                    return datetime.now() - timedelta(weeks=value)
                elif "month" in unit:
                    return datetime.now() - timedelta(days=value * 30)  # Approximation
                elif "year" in unit:
                    return datetime.now() - timedelta(days=value * 365)  # Approximation

            print(f"{Colors.WARNING}Unable to parse relative time: {relative_time}{Colors.ENDC}")
            return None
        except Exception as e:
            print(f"{Colors.FAIL}Error parsing relative time '{relative_time}': {e}{Colors.ENDC}")
            return None

    def parse_primary_description(self, description):
        """
        Parses the job's primary description to extract location, posting date, and status.
        :param description: Raw string of the primary description.
        :return: Dictionary containing location, posting date, and status.
        """
        try:
            parts = [part.strip() for part in description.split("·")]
            posted_date_str = parts[1] if len(parts) > 1 else None
            parsed_posted_date = self.parse_relative_time(posted_date_str) if posted_date_str else None

            return {
                "Location": parts[0] if len(parts) > 0 else None,
                "Posting Date": parsed_posted_date,
                "Status": parts[2] if len(parts) > 2 else None,
            }
        except Exception as e:
            print(f"{Colors.FAIL}Error parsing primary description: {e}{Colors.ENDC}")
            return {"Location": None, "Posting Date": None, "Status": None}

    def calculate_description_points(self, full_description, filters):
        """
        Calculates a score for the job based on the presence of positive, negative, and best keywords.
        :param full_description: Job description text.
        :param filters: Dictionary containing positive, negative, and best keywords.
        :return: Tuple containing points, positive words found, negative words found, and best words found.
        """
        positive_words = filters["description"]["positive"]
        negative_words = filters["description"]["negative"]
        best_words = filters["description"]["best"]

        points = 0
        pos_words_found, neg_words_found, best_words_found = [], [], []

        # Check for positive keywords
        for word in positive_words:
            if word.lower() in full_description.lower():
                points += 1
                pos_words_found.append(word)
        # Check for negative keywords
        for word in negative_words:
            if word.lower() in full_description.lower():
                points = - 1
                neg_words_found.append(word)
        # Check for best keywords
        for word in best_words:
            if word.lower() in full_description.lower():
                points = 1
                best_words_found.append(word)
        return points, pos_words_found, neg_words_found, best_words_found

    def extract_job_details(self, filters, cache):
        """
        Scrapes job details from LinkedIn and adds relevant jobs to the database.
        Skips previously viewed jobs and blacklisted companies.
        :param filters: Dictionary containing job search filters.
        :param cache: Database instance for storing job details.
        """
        total_jobs_text = self.driver.find_element(
            By.XPATH, self.xpaths["job_search"]["total_jobs"]
        ).text
        total_pages = min(
            math.ceil(int(total_jobs_text.split()[0].replace(",", "")) / 25), 40
        )
        total_scans, jobs_scanned = 0, 0
        blacklisted_jobs, irrelavant_jobs, skipped_jobs = [], [], []

        blacklisted_companies = filters.get("blacklisted_companies", [])

        loading_flag = False
        skipping_flag = False
        print(f"{Colors.HEADER}Starting job scanning...{Colors.ENDC}")
        for page in range(total_pages):
            if jobs_scanned >= filters["max_jobs"]:
                break

            # Navigate to the correct page offset
            page_offset = 25 * page
            self.driver.get(self.driver.current_url + f"&start={page_offset}")
            time.sleep(random.uniform(2, 5))  # Random sleep to avoid detection

            try:
                job_cards = self.driver.find_elements(
                    By.XPATH, self.xpaths["job_search"]["job_card"]
                )
                loading_flag = False
                for card in job_cards:
                    if jobs_scanned >= filters["max_jobs"]:
                        print(
                            f"{Colors.OKGREEN} Scanned {filters['max_jobs']} jobs as per configuration {Colors.ENDC}"
                        )
                        break

                    total_scans += 1
                    job_id = card.get_attribute("data-occludable-job-id")
                    job_link = f"https://www.linkedin.com/jobs/view/{job_id}"

                    # Skip jobs already viewed
                    if cache.query_jobs(
                        f"SELECT 1 FROM jobs WHERE job_id = '{job_id}'"
                    ):
                        skipped_jobs.append(job_id)
                        if not skipping_flag:
                            print(f"{Colors.WARNING} Skipping jobs previously viewed ...")
                            skipping_flag = True
                        continue
                    # Scroll to the job card and click it
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);", card
                    )
                    time.sleep(1)
                    card.click()
                    time.sleep(3)

                    # Extract job details
                    title = self.driver.find_element(
                        By.XPATH, self.xpaths["job_search"]["job_title"]
                    ).text
                    company = self.driver.find_element(
                        By.XPATH, self.xpaths["job_search"]["company"]
                    ).text
                    primary_description = self.driver.find_element(
                        By.XPATH, self.xpaths["job_search"]["primary_description"]
                    ).text
                    primary_dict = self.parse_primary_description(primary_description)

                    skipping_flag = False
                    
                    # Skip jobs from blacklisted companies
                    if company.lower() in [c.lower() for c in blacklisted_companies]:
                        print(
                            f"{Colors.FAIL}Blacklisted job detected: {title} at {company}{Colors.ENDC}"
                        )
                        blacklisted_jobs.append(
                            {
                                "job_id": job_id,
                                "title": title,
                                "company": company,
                                "location": primary_dict["Location"],
                                "date_posted": primary_dict["Posting Date"],
                            }
                        )
                        self.driver.back()
                        time.sleep(2)
                        continue

                    try:
                        # Expand full job description if applicable
                        show_more_button = self.driver.find_element(
                            By.XPATH, self.xpaths["job_search"]["show_more_button"]
                        )
                        self.driver.execute_script(
                            "arguments[0].click();", show_more_button
                        )
                        time.sleep(2)
                    except Exception:
                        print(f"{Colors.WARNING}Show more button not found... {Colors.ENDC}")

                    full_description_element = self.driver.find_element(
                        By.XPATH, self.xpaths["job_search"]["full_description"]
                    )
                    full_description = " ".join(
                        [
                            span.text
                            for span in full_description_element.find_elements(
                                By.TAG_NAME, "span"
                            )
                        ]
                    )

                    # Calculate job relevance points
                    points, pos, neg, best = self.calculate_description_points(
                        full_description, filters
                    )
                    level, _, _, _ = self.calculate_description_points(
                        title, filters
                    )
                    matched_keywords = [
                        word
                        for word in filters["description"]["positive"]
                        if word.lower() in full_description.lower()
                    ]

                    if points > 0 and level >=0:
                        # Save relevant job to database
                        cache.add_job(
                            job_id=job_id,
                            title=title,
                            company=company,
                            location=primary_dict["Location"],
                            date_posted=primary_dict["Posting Date"],
                            points=points,
                            matched_keywords=", ".join(matched_keywords),
                            full_description=full_description,
                            job_link=job_link,
                        )

                        # Display job details
                        print(
                            f"{Colors.OKBLUE}--------------------------------------------------------------------------------{Colors.ENDC}"
                        )
                        print(
                            f"{Colors.HEADER}Title: {title} | Company: {company} | Job ID: {job_id}{Colors.ENDC}"
                        )
                        print(
                            f"{Colors.OKGREEN}Location: {primary_dict['Location']} | Date Posted: {primary_dict['Posting Date']}{Colors.ENDC}"
                        )
                        print(
                            f"{Colors.OKCYAN}Matched Keywords: {matched_keywords}{Colors.ENDC}"
                        )
                        print(
                            f"{Colors.OKBLUE}--------------------------------------------------------------------------------{Colors.ENDC}"
                        )
                        jobs_scanned += 1
                    else:
                        print(f"{Colors.OKBLUE} Irrelavant Job {title} at {company}| {neg}{Colors.ENDC}")
                        # Mark irrelevant job
                        irrelavant_jobs.append(
                            {
                                "job_id": job_id,
                                "title": title,
                                "company": company,
                                "location": primary_dict["Location"],
                                "date_posted": primary_dict["Posting Date"],
                                "neg": neg,
                            }
                        )
                    self.driver.back()
                    time.sleep(2)  # Avoid LinkedIn rate limiting

            except Exception as e:
                if not loading_flag:
                    print(f"{Colors.WARNING}Loading Pages ...{Colors.ENDC}")
                    loading_flag = True

        # Print scan summary
        print(f"{Colors.HEADER}Job Scanning Complete{Colors.ENDC}")
        print(f"{Colors.OKCYAN}Total Jobs Scanned: {total_scans}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}Total Relevant Jobs Saved: {jobs_scanned}{Colors.ENDC}")
        print(f"{Colors.WARNING}Skipped Jobs (Previously Viewed): {len(skipped_jobs)}{Colors.ENDC}")
        print(f"{Colors.FAIL}Blacklisted Jobs: {len(blacklisted_jobs)}{Colors.ENDC}")
        print(f"{Colors.FAIL}Irrelevant Jobs: {len(irrelavant_jobs)}{Colors.ENDC}")

    def recommend_and_apply_jobs(self, cache, resume_config):
        """
        Recommends jobs based on ranking and suggests the best resume to use.
        Allows users to manually mark jobs as applied or skipped.
        :param cache: Database instance for querying job details.
        :param resume_config: Dictionary containing resume information and their associated keywords.
        """
        resumes = resume_config["resumes"]
        applications_limit = resume_config.get("applications", 0)
        applications_completed = 0

        jobs = cache.query_jobs(
            "SELECT job_id, title, company, location, points, job_link, matched_keywords FROM jobs WHERE applied = 0 ORDER BY points DESC"
        )

        print(
            f"{Colors.OKCYAN}Applications to complete: {applications_limit}{Colors.ENDC}"
        )
        for job in jobs:
            if applications_completed >= applications_limit:
                print(
                    f"{Colors.OKGREEN}Congratulations! You applied for {applications_completed} jobs.{Colors.ENDC}"
                )
                break

            job_id, title, company, location, points, job_link, matched_keywords = job
            matched_keywords_list = (
                matched_keywords.split(", ") if matched_keywords else []
            )

            # Recommend resume based on matched keywords
            suggested_resume = self.select_resume(matched_keywords_list, resumes)

            print(
                f"{Colors.OKBLUE}---------------------------------------------------------------------------{Colors.ENDC}"
            )
            print(f"{Colors.HEADER} {title} | {company} | {location}")
            print(f"{Colors.OKCYAN}{matched_keywords_list}{Colors.ENDC}")
            print(f"Link: {Colors.OKBLUE}{job_link}{Colors.ENDC}")
            print(f"Suggested Resume: {Colors.OKGREEN}{suggested_resume}{Colors.ENDC}")
            print(
                f"{Colors.OKBLUE}---------------------------------------------------------------------------{Colors.ENDC}"
            )

            # Prompt user input for application
            user_input = (
                input(
                    f" {Colors.BOLD} Did you apply for Job ID {job_id}? (yes/no): {Colors.ENDC}"
                )
                .strip()
                .lower()
            )
            if user_input == "yes":
                print(f"Marking Job ID {job_id} as applied...")
                cache.update_job_as_applied(job_id)
                applications_completed += 1
            else:
                print(f"{Colors.WARNING}Skipped Job ID {job_id}.{Colors.ENDC}")

    def select_resume(self, matched_keywords, resumes):
        """
        Selects the most appropriate resume based on matched keywords in job description.
        :param matched_keywords: List of keywords found in the job description.
        :param resumes: Dictionary of resumes and their associated keywords.
        :return: Name of the best resume file.
        """
        best_resume = None
        max_matches = 0

        for resume, keywords in resumes.items():
            matches = sum(
                1
                for keyword in matched_keywords
                if keyword.lower() in map(str.lower, keywords)
            )
            if matches > max_matches:
                best_resume = resume
                max_matches = matches

        return best_resume if best_resume else "default_resume.pdf"

    def generate_stats(self, cache):
        """
        Generates and displays statistics about the jobs in the database.
        :param cache: Database instance for querying job details.
        """
        total_jobs = cache.query_jobs("SELECT COUNT(*) FROM jobs")[0][0]
        applied_jobs = cache.query_jobs("SELECT COUNT(*) FROM jobs WHERE applied = 1")[0][0]
        unique_companies = cache.query_jobs("SELECT COUNT(DISTINCT company) FROM jobs")[0][0]

        print(f"{Colors.HEADER}Job Statistics:{Colors.ENDC}")
        print(f"Total Jobs: {total_jobs}")
        print(f"Total Applications: {applied_jobs}")
        print(f"Unique Companies: {unique_companies}")
