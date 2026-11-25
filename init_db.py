import sqlite3
import csv
import os
import glob
from pathlib import Path

# Paths
CSV_DIR = 'aqi_bulletin_csv'
DB_FILE = 'aqi.db'

def init_db():
    print("Initializing Database...")

    # Connect to SQLite
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Creating tables
    print("Creating tables...")
    cursor.executescript('''
        DROP TABLE IF EXISTS user_responses;
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS aqi_readings;
        DROP TABLE IF EXISTS cities;

        CREATE TABLE cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            state TEXT
        );

        CREATE TABLE aqi_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city_id INTEGER REFERENCES cities(id),
            date DATE NOT NULL,
            aqi INTEGER,
            prominent_pollutant TEXT,
            category TEXT
        );

        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );

        CREATE TABLE user_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            asthma TEXT,
            outdoors TEXT,
            children TEXT,
            industrial TEXT,
            season TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()

    # Loading CSVs
    print(f"Loading CSV files from {CSV_DIR}...")
    csv_files = glob.glob(os.path.join(CSV_DIR, '*.csv'))

    if not csv_files:
        print(f"No CSV files found in {CSV_DIR}. Please run the extraction script first.")
        return

    total_rows = 0
    for file_path in csv_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                city_name = row['city'].strip()
                state_name = row['state_hint'].strip() if row['state_hint'] else None
                date = row['date']
                aqi_value = int(row['aqi_value']) if row['aqi_value'].isdigit() else None
                category = row['category'].strip()
                pollutant = row['prominent_pollutant'].strip()

                if aqi_value is None:
                    continue # Skip invalid rows

                # Inserting city if it doesn't exist
                cursor.execute('SELECT id FROM cities WHERE name = ?', (city_name,))
                city_record = cursor.fetchone()

                if city_record is None:
                    cursor.execute('INSERT INTO cities (name, state) VALUES (?, ?)', (city_name, state_name))
                    city_id = cursor.lastrowid
                else:
                    city_id = city_record[0]

                # Inserting reading
                cursor.execute('''
                    INSERT INTO aqi_readings (city_id, date, aqi, prominent_pollutant, category)
                    VALUES (?, ?, ?, ?, ?)
                ''', (city_id, date, aqi_value, pollutant, category))

                total_rows += 1

    conn.commit()
    conn.close()

    print(f"Successfully loaded {total_rows} readings into {DB_FILE}!")

if __name__ == "__main__":
    init_db()
