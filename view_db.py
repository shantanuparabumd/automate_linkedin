import sqlite3

def view_db_entries(db_path="job_cache.db"):
    """View all entries in the job_cache database."""
    try:
        # Connect to the database
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        # Query to select all records
        cursor.execute("SELECT * FROM processed_jobs")

        # Fetch all entries
        rows = cursor.fetchall()

        # Print the entries
        if rows:
            print("Job IDs in the database:")
            for row in rows:
                print(f" - {row[0]}")
        else:
            print("No entries found in the database.")

    except sqlite3.Error as e:
        print(f"An error occurred while accessing the database: {e}")

    finally:
        if connection:
            connection.close()

# Usage
if __name__ == "__main__":
    view_db_entries()
