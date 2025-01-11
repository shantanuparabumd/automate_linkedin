import sqlite3
import datetime

class JobCache:
    """
    A class to manage the job database for LinkedIn job automation.

    This class provides methods to create and interact with a SQLite database 
    that stores job details. It includes functionality for adding jobs, updating 
    their application status, querying data, and managing the database connection.
    """

    def __init__(self, db_path="job_cache.db"):
        """
        Initializes the JobCache instance and creates the database table if it doesn't exist.

        Args:
            db_path (str): Path to the SQLite database file. Defaults to "job_cache.db".
        """
        self.connection = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        """
        Creates the `jobs` table in the database if it does not already exist.

        The table includes the following columns:
        - `job_id`: Unique identifier for the job (Primary Key).
        - `title`: Job title.
        - `company`: Company offering the job.
        - `location`: Job location.
        - `date_posted`: Date the job was posted.
        - `points`: A score assigned to the job based on keyword matching.
        - `matched_keywords`: Keywords from the job description that matched user-defined filters.
        - `full_description`: Full job description.
        - `job_link`: URL to the job posting.
        - `applied`: Boolean flag indicating if the job has been applied to.
        - `date_applied`: Date the job was marked as applied.
        """
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

    def add_job(
        self,
        job_id,
        title,
        company,
        location,
        date_posted,
        points,
        matched_keywords,
        full_description,
        job_link,
    ):
        """
        Adds a job to the database if it doesn't already exist.

        Args:
            job_id (str): Unique identifier for the job.
            title (str): Job title.
            company (str): Company offering the job.
            location (str): Job location.
            date_posted (str): Date the job was posted.
            points (int): Score assigned to the job based on keyword matching.
            matched_keywords (str): Comma-separated list of matched keywords.
            full_description (str): Full job description.
            job_link (str): URL to the job posting.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO jobs 
            (job_id, title, company, location, date_posted, points, matched_keywords, full_description, job_link)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                job_id,
                title,
                company,
                location,
                date_posted,
                points,
                matched_keywords,
                full_description,
                job_link,
            ),
        )
        self.connection.commit()

    def update_job_as_applied(self, job_id):
        """
        Marks a job as applied and sets the date it was applied.

        Args:
            job_id (str): Unique identifier for the job.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            UPDATE jobs SET applied = 1, date_applied = ? WHERE job_id = ?
        """,
            (datetime.date.today().isoformat(), job_id),
        )
        self.connection.commit()

    def query_jobs(self, query):
        """
        Executes a custom SQL query on the `jobs` table.

        Args:
            query (str): The SQL query to execute.

        Returns:
            list: Results of the query as a list of tuples.
        """
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def close(self):
        """
        Closes the database connection.
        """
        self.connection.close()
