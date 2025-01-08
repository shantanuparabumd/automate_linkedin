from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import yaml
import pandas as pd
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import math
import random

# Setup WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# Load credentials from YAML
with open('credentials.yaml', 'r') as f:
    credentials = yaml.safe_load(f)

# --- LinkedIn Login ---
def login_linkedin(driver, email, password):
    driver.get("https://www.linkedin.com/login")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))
    driver.find_element(By.ID, "username").send_keys(email)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(5)

# --- Job Search ---
def search_jobs(driver, keywords):
    query = "%20AND%20".join(keywords)  # LinkedIn uses %20 for spaces
    driver.get(f"https://www.linkedin.com/jobs/search/?keywords={query}")
    time.sleep(5)


def parse_primary_description(description):
    # Split the description by the separator '·'
    parts = [part.strip() for part in description.split('·')]
    
    # Assign the parts to respective fields
    location = parts[0] if len(parts) > 0 else None
    posting_date = parts[1] if len(parts) > 1 else None
    status = parts[2] if len(parts) > 2 else None
    
    return {
        "Location": location,
        "Posting Date": posting_date,
        "Status": status
    }
# --- Extract Job Data ---
def extract_job_details(driver):
    job_data = []
    
    # Get total jobs from the header
    totalJobs = driver.find_element(By.XPATH, '//small').text
    totalPages = jobsToPages(totalJobs)

    for page in range(totalPages):
        if len(job_data)> 5:
            break
        # Update URL for pagination
        pageOffset = 25 * page
        driver.get(driver.current_url + f"&start={pageOffset}")
        time.sleep(random.uniform(2, 5))  # Random sleep to avoid detection
        
        # Extract job cards
        job_cards = driver.find_elements(By.XPATH, '//li[@data-occludable-job-id]')
        
        for card_index, card in enumerate(job_cards):
            
            if len(job_data)> 5:
                break
            try:
                # Scroll to the job card for visibility
                driver.execute_script("arguments[0].scrollIntoView(true);", card)
                time.sleep(1)

                # Click the job card to open it in full view
                card.click()
                time.sleep(3)  # Allow time for the full view to load

                
                # Extract detailed job information
                title = driver.find_element(By.XPATH, '//h1[contains(@class, "t-24 t-bold")]').text
                print("Extracted the following", title)

                # <div class="job-details-jobs-unified-top-card__company-name" dir="ltr">
                #   <a class="TSUUmBLgCBYgbinAiiknGsAHecRSeNvu " target="_self" href="https://www.linkedin.com/company/flightwave-aerospace-systems/life" data-test-app-aware-link=""><!---->FlightWave Aerospace<!----></a>
                # </div>
                company = driver.find_element(By.XPATH, '//div[contains(@class, "job-details-jobs-unified-top-card__company-name")]//a').text
                print("Company Name:", company)

                # Primary description
                primary_description = driver.find_element(By.XPATH, '//div[contains(@class, "job-details-jobs-unified-top-card__primary-description-container")]').text
                
                primary_dict = parse_primary_description(primary_description)

                print(primary_dict)


                # Expand "Show More" section if available
                try:
                    show_more_button = driver.find_element(By.XPATH, '//button[contains(@class, "feed-shared-inline-show-more-text__see-more-less-toggle")]')
                    driver.execute_script("arguments[0].click();", show_more_button)
                    time.sleep(2)
                except:
                    pass  # If the button is not available, continue

                # Full job description
                # Full job description
                full_description_element = driver.find_element(By.XPATH, '//div[contains(@class, "feed-shared-inline-show-more-text--expanded")]')
                full_description = " ".join([span.text for span in full_description_element.find_elements(By.TAG_NAME, "span")])

                print(full_description)
                # Save job details to the list
                job_data.append({
                    'Title': title,
                    'Company': company,
                    'Location': primary_dict['Location'],
                    # 'Posting': primary_dict['Posting Date'],
                    # 'Status': primary_dict['Status'],
                    # 'Full Description': full_description
                })

                # Navigate back to the job list
                driver.back()
                time.sleep(2)

            except Exception as e:
                print(f"Error processing job card at index")
    
    return job_data

# --- Helper Function for Pagination ---
def jobsToPages(numOfJobs: str) -> int:
    total_jobs = int(numOfJobs.split()[0].replace(',', ''))  # Extract the number of jobs
    pages = math.ceil(total_jobs / 25)
    return min(pages, 40)  # Limit to 40 pages (LinkedIn's max)

# Main execution starts here
if __name__ == "__main__":
    try:
        login_linkedin(driver, credentials['email'], credentials['password'])
        keywords = credentials['keywords']
        search_jobs(driver, keywords)
        job_details = extract_job_details(driver)

        # Save data to CSV
        df = pd.DataFrame(job_details)
        df.to_csv('linkedin_full_jobs.csv', index=False)
        print("Job data successfully saved to linkedin_full_jobs.csv")
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        driver.quit()



