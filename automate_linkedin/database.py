import sqlite3
import datetime
import csv
import os


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class JobViewer:
    def __init__(self, db_path="job_cache.db"):
        self.connection = sqlite3.connect(db_path)

    def query_jobs(self, query):
        """
        Run a custom query on the jobs database.
        """
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def update_job_score(self, job_id, increment):
        """
        Increment the score of a job by a specified amount.
        """
        cursor = self.connection.cursor()
        cursor.execute("UPDATE jobs SET points = points + ? WHERE job_id = ?", (increment, job_id))
        self.connection.commit()

    def export_to_csv(self, output_file="jobs.csv"):
        """
        Export selected job details to a CSV file, deleting any existing file first.
        """
        try:
            # Delete the existing file if it exists
            if os.path.exists(output_file):
                os.remove(output_file)

            # Query the database for selected fields
            jobs = self.query_jobs("SELECT title, company, location, date_posted, applied, job_link FROM jobs")

            # Define column headers
            headers = ["Title", "Company", "Location", "Date Posted", "Applied", "Link"]

            # Write to CSV
            with open(output_file, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(headers)  # Write header row
                writer.writerows(jobs)   # Write job rows

            print(f"{Colors.OKGREEN}Database exported to {output_file}.{Colors.ENDC}")

        except Exception as e:
            print(f"{Colors.FAIL}Error exporting database to CSV: {e}{Colors.ENDC}")

    def analyze_jobs(self):
        """
        Analyze applied and pending jobs, and detect high-ranking pending jobs close to their expiration.
        """
        try:
            # Fetch job statistics
            total_jobs = self.query_jobs("SELECT COUNT(*) FROM jobs")[0][0]
            applied_jobs = self.query_jobs("SELECT COUNT(*) FROM jobs WHERE applied = 1")[0][0]
            pending_jobs = self.query_jobs("SELECT COUNT(*) FROM jobs WHERE applied = 0")[0][0]

            print(f"{Colors.HEADER}Job Analysis:{Colors.ENDC}")
            print(f"Total Jobs: {Colors.OKBLUE}{total_jobs}{Colors.ENDC}")
            print(f"Applied Jobs: {Colors.OKCYAN}{applied_jobs}{Colors.ENDC}")
            print(f"Pending Jobs: {Colors.OKGREEN}{pending_jobs}{Colors.ENDC}")

            # Detect high-ranking jobs close to their expiration
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
                    try:
                        # Parse datetime and calculate the difference in days
                        posted_datetime = datetime.datetime.strptime(date_posted, "%Y-%m-%d %H:%M:%S.%f")
                        days_since_posted = (today - posted_datetime).days

                        # If a job is more than 25 days old, it's considered close to expiring
                        if days_since_posted > 25:
                            expiring_jobs.append({
                                "job_id": job_id,
                                "title": title,
                                "company": company,
                                "date_posted": date_posted,
                                "points": points,
                            })
                            # Increase the score of the job for prioritization
                            self.update_job_score(job_id, 5)
                    except ValueError as e:
                        print(f"{Colors.WARNING}Error parsing date for job {job_id}: {e}{Colors.ENDC}")

            if expiring_jobs:
                print(f"\n{Colors.WARNING}High-ranking jobs close to expiration:{Colors.ENDC}")
                for job in expiring_jobs:
                    print(f"Job ID: {job['job_id']}, Title: {job['title']}, "
                          f"Company: {job['company']}, Date Posted: {job['date_posted']}, "
                          f"Points: {job['points']} -> {job['points'] + 5}")
            else:
                print(f"{Colors.OKCYAN}No high-ranking jobs close to expiration.{Colors.ENDC}")

        except Exception as e:
            print(f"{Colors.FAIL}Error analyzing jobs: {e}{Colors.ENDC}")

    def close(self):
        self.connection.close()


def main():
    viewer = JobViewer()

    try:
        # Analyze jobs
        viewer.analyze_jobs()

        # Optional: Export to CSV
        export_csv = input(f"{Colors.BOLD}Would you like to export the database to CSV? (yes/no): {Colors.ENDC}").strip().lower()
        if export_csv == "yes":
            viewer.export_to_csv()

    except Exception as e:
        print(f"{Colors.FAIL}An error occurred: {e}{Colors.ENDC}")

    finally:
        viewer.close()


if __name__ == "__main__":
    main()
