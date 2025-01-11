# `database.py` - Job Database Analysis and Management

The `database.py` script is designed to analyze and manage the job database created by the LinkedIn job automation tool. It provides utilities to:
- Analyze the database for insights, such as pending jobs and high-priority jobs nearing expiration.
- Export the database to a CSV file for easy viewing and editing in tools like Excel or Google Sheets.
- Increment scores for jobs nearing expiration to prioritize them for future actions.

---

## Features

### 1. **Analyze Jobs**
The script scans the database to:
- Count the total number of jobs, applied jobs, and pending jobs.
- Identify high-priority jobs that are nearing expiration (older than 25 days).
- Increment the scores of jobs nearing expiration to ensure they are prioritized in the `apply` mode.

---

### 2. **Export Database to CSV**
- Exports the database to a `jobs.csv` file.
- The CSV file includes columns like title, company, location, date posted, whether the job is applied, and the job link.
- Deletes any existing CSV file before creating a new one to ensure the data is up to date.

---

## How It Works

### **Database Analysis**
The script connects to the `job_cache.db` SQLite database and performs the following tasks:
1. Counts total jobs, applied jobs, and pending jobs.
2. Analyzes pending jobs to identify those older than 25 days (based on the `date_posted` field).
3. Increments the scores of jobs nearing expiration by 5 points to prioritize them.

### **Export to CSV**
- Queries the database to retrieve job details.
- Writes the results to a CSV file named `jobs.csv`.

---

## Example Output

### **Console Output**
When you run `database.py`, you will see:
```plaintext
Job Analysis:
Total Jobs: 150
Applied Jobs: 50
Pending Jobs: 100

High-ranking jobs close to expiration:
Job ID: 123456, Title: Robotics Engineer, Company: ABC Robotics, 
Date Posted: 2025-01-01, Points: 10 -> 15
Job ID: 234567, Title: Machine Learning Engineer, Company: XYZ AI, 
Date Posted: 2025-01-02, Points: 12 -> 17
```

### **CSV File**
The exported CSV (`jobs.csv`) will look like this:
| Title                     | Company       | Location      | Date Posted        | Applied | Link                                    |
|---------------------------|---------------|---------------|--------------------|---------|-----------------------------------------|
| Robotics Engineer         | ABC Robotics  | New York, NY  | 2025-01-01 12:00:00| No      | https://www.linkedin.com/jobs/view/1234|
| Machine Learning Engineer | XYZ AI        | Remote        | 2025-01-02 08:00:00| Yes     | https://www.linkedin.com/jobs/view/2345|

---

## Code Walkthrough

### **1. Job Analysis**
The `analyze_jobs` function performs the following tasks:
- Counts jobs in various states (total, applied, pending).
- Identifies pending jobs older than 25 days.
- Increments the scores of expiring jobs for prioritization.

```python
def analyze_jobs(self):
    total_jobs = self.query_jobs("SELECT COUNT(*) FROM jobs")[0][0]
    applied_jobs = self.query_jobs("SELECT COUNT(*) FROM jobs WHERE applied = 1")[0][0]
    pending_jobs = self.query_jobs("SELECT COUNT(*) FROM jobs WHERE applied = 0")[0][0]

    # Identify jobs close to expiration
    today = datetime.datetime.now()
    expiring_jobs = []
    pending_jobs_query = """
        SELECT job_id, title, company, date_posted, points 
        FROM jobs 
        WHERE applied = 0 
        ORDER BY points DESC
    """
    pending_jobs_list = self.query_jobs(pending_jobs_query)

    for job_id, title, company, date_posted, points in pending_jobs_list:
        if date_posted:
            posted_datetime = datetime.datetime.strptime(date_posted, "%Y-%m-%d %H:%M:%S.%f")
            days_since_posted = (today - posted_datetime).days
            if days_since_posted > 25:
                expiring_jobs.append({
                    "job_id": job_id,
                    "title": title,
                    "company": company,
                    "date_posted": date_posted,
                    "points": points,
                })
                self.update_job_score(job_id, 5)  # Increment score by 5
```

### **2. Export to CSV**
The `export_to_csv` function fetches job details from the database and writes them to a CSV file.

```python
def export_to_csv(self, output_file="jobs.csv"):
    if os.path.exists(output_file):
        os.remove(output_file)  # Delete existing file

    jobs = self.query_jobs("SELECT title, company, location, date_posted, applied, job_link FROM jobs")
    headers = ["Title", "Company", "Location", "Date Posted", "Applied", "Link"]

    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(jobs)
```

---

## How to Use

### **Running the Script**
1. Open your terminal or command prompt.
2. Navigate to the project directory.
3. Run the script:
   ```bash
   python database.py
   ```

### **Features**
- **Analyze Jobs**:
  - Displays the total number of jobs, applied jobs, and pending jobs.
  - Highlights high-priority jobs nearing expiration and increments their scores.
- **Export to CSV**:
  - After analyzing, the script will prompt you to export the database to a CSV file.

---

## Notes

- The database file (`job_cache.db`) is the source of truth. Ensure it's updated by running the `automate.py` script in `scan` mode before analyzing.
- Always generate a new CSV after modifying the database to ensure the data reflects the latest changes.

For more information, visit the [Main README](../README.md).
```