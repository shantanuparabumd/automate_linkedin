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
        time.sleep(15)

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


    def apply_to_job(self, description, filters, cache):
        """Handles Easy Apply, answering questions and uploading resumes."""
        try:
            # Find Easy Apply button and click
            easy_apply_button = self.driver.find_element(By.XPATH, self.xpaths["job_apply"]["easy_apply_button"])
            easy_apply_button.click()
            print(f"{Colors.OKCYAN}Clicked Easy Apply button{Colors.ENDC}")
            time.sleep(2)

            self.handle_easy_apply_form()
            # Load answers for questions from YAML
            answers = filters.get("answers", {})

            # Answer questions
            while True:
                try:
                    question_element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, self.xpaths["job_apply"]["question_text"]))
                    )
                    question_text = question_element.text.strip()
                    print(f"{Colors.OKBLUE}Question: {question_text}{Colors.ENDC}")

                    answer = answers.get(question_text, None)
                    if answer:
                        print(f"{Colors.OKGREEN}Answer: {answer}{Colors.ENDC}")
                        input_field = self.driver.find_element(By.XPATH, self.xpaths["job_apply"]["answer_field"])
                        input_field.send_keys(answer)
                    else:
                        print(f"{Colors.WARNING}No answer found for question: {question_text}{Colors.ENDC}")
                        continue

                    next_button = self.driver.find_element(By.XPATH, self.xpaths["job_apply"]["next_button"])
                    if next_button:
                        next_button.click()
                        time.sleep(2)
                    else:
                        print("No 'Next' button. Breaking loop.")
                        break
                except Exception as e:
                    print(f"Error answering question: {e}")
                    break

            # Upload resume
            resume = self.select_resume(description, filters["resumes"])
            upload_input = self.driver.find_element(By.XPATH, self.xpaths["job_apply"]["upload_resume"])
            upload_input.send_keys(resume)
            print(f"{Colors.OKCYAN}Uploaded resume: {resume}{Colors.ENDC}")

            # Submit application
            submit_button = self.driver.find_element(By.XPATH, self.xpaths["job_apply"]["submit_button"])
            submit_button.click()
            print(f"{Colors.OKGREEN}Application submitted successfully!{Colors.ENDC}")

        except Exception as e:
            print(f"{Colors.FAIL}Error during Easy Apply: {e}{Colors.ENDC}")

    def select_resume(self, description, resume_config):
        """Selects the appropriate resume based on keywords."""
        selected_resume = resume_config.get("default", "default_resume.pdf")
        description = description.lower()

        for resume_name, keywords in resume_config.items():
            if any(keyword.lower() in description for keyword in keywords):
                selected_resume = resume_name
                break

        print(f"Resume selected: {Colors.OKBLUE}{selected_resume}{Colors.ENDC}")
        return selected_resume
    
    def extract_questions_from_form(self):
        """
        Extracts all questions from the LinkedIn Easy Apply form, including:
        1. Text input questions with associated labels.
        2. Radio button questions with options.
        """
        try:
            print(f"{Colors.HEADER}Extracting all questions from the form...{Colors.ENDC}")

            # Extract text input questions
            text_questions = self.driver.find_elements(By.XPATH, '//div[contains(@data-test-single-line-text-form-component, "true")]')
            for text_question in text_questions:
                try:
                    question_text = text_question.find_element(By.XPATH, './/label').text.strip()
                    print(f"{Colors.OKBLUE}Text Input Question Found: {question_text}{Colors.ENDC}")

                    # Check for associated input field
                    input_field = text_question.find_element(By.XPATH, './/input')
                    if input_field:
                        print(f"{Colors.OKCYAN}Input Field Detected for: {question_text}{Colors.ENDC}")
                    else:
                        print(f"{Colors.WARNING}No Input Field Detected for: {question_text}{Colors.ENDC}")
                except Exception as e:
                    print(f"{Colors.FAIL}Error processing text question: {e}{Colors.ENDC}")

            # Extract radio button questions
            radio_questions = self.driver.find_elements(By.XPATH, '//fieldset[contains(@data-test-form-builder-radio-button-form-component, "true")]')
            for radio_question in radio_questions:
                try:
                    question_text = radio_question.find_element(By.XPATH, './legend/span[1]').text.strip()
                    print(f"{Colors.OKCYAN}Radio Button Question Found: {question_text}{Colors.ENDC}")

                    # List available options
                    options = radio_question.find_elements(By.XPATH, './/div[contains(@class, "display-flex")]/label')
                    options_text = [option.text.strip() for option in options]
                    print(f"{Colors.BOLD}Options: {options_text}{Colors.ENDC}")
                except Exception as e:
                    print(f"{Colors.FAIL}Error processing radio question: {e}{Colors.ENDC}")

        except Exception as e:
            print(f"{Colors.FAIL}Error extracting questions from the form: {e}{Colors.ENDC}")


    def handle_easy_apply_form(self):
        """
        Handles the Easy Apply form:
        1. Logs all detected questions (radio, text input).
        2. Handles 'Next', 'Review', and 'Submit' buttons dynamically.
        3. If 'Next' or 'Review' buttons are not found in 3 attempts, clicks 'Dismiss' and then 'Discard'.
        """
        unanswered_questions = []
        attempts = 0

        try:
            while attempts < 6:
                print(f"Attempts {attempts}")
                self.extract_questions_from_form()

                # Handle navigation: "Next" or "Review" button
                try:
                    next_or_review_button = self.driver.find_element(By.XPATH, '//button[@aria-label="Continue to next step" or @aria-label="Review your application"]')
                    next_or_review_button.click()
                    print(f"{Colors.OKCYAN}Clicked 'Next' or 'Review' button.{Colors.ENDC}")
                    attempts += 1
                    time.sleep(2)
                except Exception as e:
                    attempts += 1
                    print(f"{Colors.WARNING}No 'Next' or 'Review' button found, attempt {attempts}: {e}{Colors.ENDC}")
            if attempts >= 6:
                print(f"{Colors.FAIL}Exceeded maximum attempts to find 'Next' or 'Review' button.{Colors.ENDC}")
                self.handle_dismiss_and_discard()
                return

            # After "Review", click 'Submit Application'
            try:
                submit_button = self.driver.find_element(By.XPATH, '//button[contains(text(), "Submit application")]')
                submit_button.click()
                print(f"{Colors.OKGREEN}Application submitted successfully!{Colors.ENDC}")
            except Exception as e:
                print(f"{Colors.FAIL}No 'Submit Application' button found: {e}{Colors.ENDC}")

        except Exception as e:
            print(f"{Colors.FAIL}Error handling Easy Apply form: {e}{Colors.ENDC}")

        # Log unanswered questions
        if unanswered_questions:
            print(f"{Colors.WARNING}Unanswered Questions:{Colors.ENDC}")
            for question in unanswered_questions:
                print(f" - {Colors.FAIL}{question}{Colors.ENDC}")


    def handle_dismiss_and_discard(self):
        """
        Handles the dismissal of the Easy Apply form:
        1. Clicks the 'Dismiss' button.
        2. Clicks the 'Discard' button in the discard modal.
        """
        try:
            # Find and click the 'Dismiss' button
            dismiss_button = self.driver.find_element(By.XPATH, '//button[@aria-label="Dismiss"]')
            dismiss_button.click()
            print(f"{Colors.OKCYAN}Clicked 'Dismiss' button.{Colors.ENDC}")
            time.sleep(2)

            # Find and click the 'Discard' button
            discard_button = self.driver.find_element(By.XPATH, '//button[contains(@data-control-name, "discard_application_confirm_btn")]')
            discard_button.click()
            print(f"{Colors.OKCYAN}Clicked 'Discard' button to confirm dismissal.{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}Error handling dismissal and discard: {e}{Colors.ENDC}")



                
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
                    

                    self.apply_to_job(full_description, filters, cache)

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
