import sqlite3
import yaml
import json
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
    def __init__(self, db_path="job_cache.db", resume_yaml="configs/resume.yaml", applied_jobs_file="configs/applied_jobs.json"):
        self.connection = sqlite3.connect(db_path)
        self.resume_config = self.load_resume_config(resume_yaml)
        self.applied_jobs_file = applied_jobs_file
        self.applied_jobs = self.load_applied_jobs()

    def load_resume_config(self, resume_yaml):
        """
        Load resume keywords from the YAML file.
        """
        with open(resume_yaml, 'r') as f:
            return yaml.safe_load(f)

    def load_applied_jobs(self):
        """
        Load applied jobs from a JSON file.
        """
        if os.path.exists(self.applied_jobs_file):
            with open(self.applied_jobs_file, 'r') as f:
                return set(json.load(f))
        return set()

    def save_applied_jobs(self):
        """
        Save applied jobs to a JSON file.
        """
        with open(self.applied_jobs_file, 'w') as f:
            json.dump(list(self.applied_jobs), f)

    def mark_job_as_applied(self, job_id):
        """
        Mark a job as applied and save it to the applied jobs file.
        """
        self.applied_jobs.add(job_id)
        self.save_applied_jobs()
        print(f"{Colors.OKGREEN}Marked Job ID {job_id} as applied.{Colors.ENDC}")

    def export_jobs_to_yaml(self, output_file="jobs.yaml"):
        """
        Exports all jobs from the database into a YAML file for manual management.
        """
        try:
            jobs = self.query_jobs("SELECT job_id, title, company, location, points, matched_keywords, date_posted FROM jobs")
            job_list = []

            for job in jobs:
                job_id, title, company, location, points, matched_keywords, date_posted = job
                job_list.append({
                    "job_id": job_id,
                    "title": title,
                    "company": company,
                    "location": location,
                    "points": points,
                    "matched_keywords": matched_keywords.split(", ") if matched_keywords else [],
                    "date_posted": date_posted,
                    "applied": False  # Mark as not applied by default
                })

            with open(output_file, 'w') as f:
                yaml.dump(job_list, f, default_flow_style=False)

            print(f"{Colors.OKGREEN}Exported jobs to {output_file}.{Colors.ENDC}")

        except Exception as e:
            print(f"{Colors.FAIL}Error exporting jobs to YAML: {e}{Colors.ENDC}")

    def filter_jobs_from_yaml(self, input_file="jobs.yaml"):
        """
        Loads jobs from a YAML file and filters out jobs marked as applied.
        """
        try:
            with open(input_file, 'r') as f:
                jobs = yaml.safe_load(f)

            filtered_jobs = [job for job in jobs if not job.get("applied", False)]
            print(f"{Colors.OKGREEN}Filtered out applied jobs.{Colors.ENDC}")
            return filtered_jobs

        except Exception as e:
            print(f"{Colors.FAIL}Error filtering jobs from YAML: {e}{Colors.ENDC}")
            return []

    def rank_jobs_by_points(self):
        """
        Ranks jobs by points and determines the best resume to use.
        Excludes applied jobs.
        """
        try:
            non_applied_jobs = self.filter_jobs_from_yaml()
            print(f"{Colors.HEADER}Ranking of Non-Applied Jobs by Points:{Colors.ENDC}")

            for job in sorted(non_applied_jobs, key=lambda x: x["points"], reverse=True):
                print(f"{Colors.BOLD}Job ID: {job['job_id']}{Colors.ENDC}")
                print(f"Title: {Colors.OKBLUE}{job['title']}{Colors.ENDC}")
                print(f"Company: {Colors.OKCYAN}{job['company']}{Colors.ENDC}")
                print(f"Location: {Colors.OKGREEN}{job['location']}{Colors.ENDC}")
                print(f"Points: {Colors.WARNING}{job['points']}{Colors.ENDC}")
                print(f"Matched Keywords: {Colors.OKBLUE}{job['matched_keywords']}{Colors.ENDC}")
                print(f"Date Posted: {Colors.OKCYAN}{job['date_posted']}{Colors.ENDC}")

                # Determine the best resume to use
                best_resume = self.select_best_resume(job["matched_keywords"])
                print(f"{Colors.OKGREEN}Best Resume to Use: {best_resume}{Colors.ENDC}")
                print("-" * 50)

        except Exception as e:
            print(f"{Colors.FAIL}Error ranking jobs: {e}{Colors.ENDC}")

    def select_best_resume(self, matched_keywords):
        """
        Selects the best resume based on the matched keywords.
        """
        best_resume = None
        best_score = 0

        for resume_name, keywords in self.resume_config.items():
            score = sum(1 for keyword in matched_keywords if keyword.lower() in map(str.lower, keywords))
            if score > best_score:
                best_resume = resume_name
                best_score = score

        return best_resume or "default_resume.pdf"

    def query_jobs(self, query):
        """
        Run a custom query on the jobs database.
        """
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def close(self):
        self.connection.close()


def main():
    viewer = JobViewer()

    try:
        # Export all jobs to YAML
        viewer.export_jobs_to_yaml()

        # Display non-applied jobs ranked by points
        viewer.rank_jobs_by_points()

    except Exception as e:
        print(f"{Colors.FAIL}An error occurred: {e}{Colors.ENDC}")

    finally:
        viewer.close()


if __name__ == "__main__":
    main()
