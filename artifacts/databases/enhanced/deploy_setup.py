import os
import mysql.connector
from dotenv import load_dotenv
import subprocess

# Load environment variables from .env (optional)
load_dotenv()

# Database connection parameters
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "rma_db"),
    "port": int(os.getenv("DB_PORT", 3306))
}

def run_sql_script(path):
    with open(path, "r") as f:
        sql_script = f.read()

    # Split script on semicolon and execute each command
    statements = [stmt.strip() for stmt in sql_script.split(";") if stmt.strip()]

    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()

    for stmt in statements:
        try:
            cursor.execute(stmt)
        except mysql.connector.Error as err:
            print(f"Error executing: {stmt}\n{err}")

    connection.commit()
    cursor.close()
    connection.close()
    print("Database schema and procedures initialized successfully.")

def seed_data():
    try:
        subprocess.run(["python", "deploy_seed.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running deploy_seed.py: {e}")

if __name__ == "__main__":
    run_sql_script("sql/setup_database.sql")
    seed_data()
