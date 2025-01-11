# XPath Configuration (`xpaths.yaml`)

This file contains the XPath definitions for identifying and interacting with various HTML elements on LinkedIn during the scraping process. The use of a separate `xpaths.yaml` allows for easy updates if LinkedIn changes its HTML structure, ensuring the scraper remains functional.

---

## Structure of `xpaths.yaml`

### **1. Login Section**
XPaths for handling the LinkedIn login page.

```yaml
login:
  username: "//input[@id='username']"   # XPath for the username input field.
  password: "//input[@id='password']"   # XPath for the password input field.
  submit: "//button[@type='submit']"    # XPath for the login button.
```

---

### **2. Job Search Section**
XPaths used for navigating and extracting job-related data from LinkedIn job search pages.

```yaml
job_search:
  total_jobs: "//small"  # XPath for the total number of jobs displayed in the search results.
  job_card: "//li[@data-occludable-job-id]"  # XPath for individual job cards in the search results.
  job_title: "//h1[contains(@class, 't-24 t-bold')]"  # XPath for the job title on the job details page.
  company: "//div[contains(@class, 'job-details-jobs-unified-top-card__company-name')]//a"  # XPath for the company name.
  primary_description: "//div[contains(@class, 'job-details-jobs-unified-top-card__primary-description-container')]"  
    # XPath for extracting the job's location, posting date, and status.
  show_more_button: "//button[contains(@class, 'feed-shared-inline-show-more-text__see-more-less-toggle')]"  
    # XPath for expanding hidden sections of the job description.
  full_description: "//div[contains(@class, 'feed-shared-inline-show-more-text--expanded')]"  
    # XPath for the full job description after expanding.
```

---

### **3. Job Application Section**
XPaths for handling the Easy Apply feature on LinkedIn.

```yaml
job_apply:
  easy_apply_button: "//button[contains(@aria-label, 'Easy Apply') and contains(@class, 'jobs-apply-button')]"  
    # XPath for the Easy Apply button.
  question_text: "//div[contains(@class, 'jobs-easy-apply-form__question')]"  
    # XPath for extracting questions during the Easy Apply process.
  answer_field: "//input[contains(@class, 'jobs-easy-apply-form__input')]"  
    # XPath for input fields to answer Easy Apply questions.
  next_button: "//button[contains(text(), 'Next')]"  
    # XPath for the "Next" button during the Easy Apply process.
  upload_resume: "//input[@type='file']"  
    # XPath for the file input field to upload resumes.
  submit_button: "//button[contains(text(), 'Submit application')]"  
    # XPath for the final submission button in the Easy Apply process.
```

---

## Example File

```yaml
login:
  username: "//input[@id='username']"
  password: "//input[@id='password']"
  submit: "//button[@type='submit']"

job_search:
  total_jobs: "//small"
  job_card: "//li[@data-occludable-job-id]"
  job_title: "//h1[contains(@class, 't-24 t-bold')]"
  company: "//div[contains(@class, 'job-details-jobs-unified-top-card__company-name')]//a"
  primary_description: "//div[contains(@class, 'job-details-jobs-unified-top-card__primary-description-container')]"
  show_more_button: "//button[contains(@class, 'feed-shared-inline-show-more-text__see-more-less-toggle')]"
  full_description: "//div[contains(@class, 'feed-shared-inline-show-more-text--expanded')]"

job_apply:
  easy_apply_button: "//button[contains(@aria-label, 'Easy Apply') and contains(@class, 'jobs-apply-button')]"
  question_text: "//div[contains(@class, 'jobs-easy-apply-form__question')]"
  answer_field: "//input[contains(@class, 'jobs-easy-apply-form__input')]"
  next_button: "//button[contains(text(), 'Next')]"
  upload_resume: "//input[@type='file']"
  submit_button: "//button[contains(text(), 'Submit application')]"
```

---

## How It Works

1. **Login Process**
   - The script uses the `login` section to interact with LinkedIn's login page elements.

2. **Job Search**
   - The `job_search` section defines the XPaths for extracting job-related details like title, company, and description.

3. **Easy Apply**
   - The `job_apply` section helps automate the Easy Apply process by interacting with LinkedIn's application form elements.

---

## Why Use `xpaths.yaml`?

- LinkedIn's UI frequently changes, which can break hardcoded XPaths.
- This configuration file allows you to quickly update XPaths without modifying the script.
- Ensures maintainability and adaptability of the scraper.

---

For more details on configuring the script, visit the [Main README](../README.md).
