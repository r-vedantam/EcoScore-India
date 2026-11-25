# EcoScore India
#### Video Demo:  <https://youtu.be/rudNUcau90I>
#### Description:

**EcoScore India** is a comprehensive full-stack web application built for my CS50x Final Project. It transforms complex, raw Air Quality Index (AQI) data from the Central Pollution Control Board (CPCB) of India into an intuitive, personalized, and visually appealing dashboard.

Instead of just showing raw AQI numbers (which can be non-linear), this project introduces the **EcoQI Score**, a 0 to 100 grading system where 100 is perfectly clean air. The app allows users to view national leaderboards, compare cities side-by-side, view historical trends, and even receive a "Personalized Ranking" based on their specific health sensitivities and seasonal travel plans.

---

## 1. The Data Pipeline

The most challenging and crucial part of this project was acquiring and structuring the data. The CPCB releases daily air quality bulletins as raw PDF files, which are difficult for databases to read:

### Step 1: PDF Extraction (Unstructured to Structured Data)
The raw data started as daily PDF files (`AQI_Bulletin_YYYYMMDD.pdf`) published by the government. I wrote a Python automation script using the PDF parsing library: `pdfplumber` to scan through hundreds of pages of these bulletins.
The script allowed skipping headers and empty rows, extracted the table data (City, State, AQI Value, Prominent Pollutant), normalized strings, and finally exported **CSV files** (Comma Separated Values) for each day of the year.

### Step 2: Database Initialization (`init_db.py`)
Once the clean CSVs were generated, they needed to be stored in a database file.
I created another script `init_db.py`, which uses Python's built-in `sqlite3` library to:
1. Create a relational schema in `aqi.db` with tables for `cities`, `aqi_readings`, `users`, and `user_responses`.
2. Loop through every single generated CSV file in the `aqi_bulletin_csv` folder.
3. Insert unique cities into the `cities` table (generating a `city_id`).
4. Insert a lot of daily records into the `aqi_readings` table, linked to the correct city.

## 2. Application Architecture

The backend is powered by **Python and Flask**. The frontend utilizes **Bootstrap 5** for a responsive, mobile-enabled design, featuring a custom "Glacier" CSS theme override. I drew some inspiration from the finance project, using 'apology.html' and '@login_required' decorator.

### The EcoQI Algorithm
Raw AQI scales from 0 to 500+, where lower is better. To make this intuitive, `helpers.py` contains the `calculate_ecoqi(aqi)` function. This applies a piecewise mathematical transformation to invert the AQI into a 0-100 score and helps in assigning a letter grade.
* Example: An AQI of 45 (Good) becomes an EcoQI of 82 (Grade A). An AQI of 350 (Severe) drops the EcoQI to 3 (Grade F).

### Interactive Features
- **The Leaderboard (`/`)**: Queries the database to find the average AQI for every city, calculates the EcoQI grade, and displays them in a searchable table. JavaScript is used to instantly filter table rows by city name without reloading the page.
- **City Details (`/city/<id>`)**: Shows a specific city's summary stats (Best day, Worst day, Top Pollutant) and a chronological table of daily readings.
- **Personalized Ranking (`/rank`)**: A questionnaire that asks users about asthma, children, or industrial sensitivity. Based on the POST request answers, the backend applies weighted multipliers to the AQI scores (e.g., heavily penalizing PM2.5 for asthma sufferers) and re-sorts the leaderboard to show the best cities *for them* sortable by season.
- **City Comparison (`/compare`)**: Uses two dropdowns to allow side-by-side metric comparison of any two cities and declares a "Winner".

## 3. Project Structure

```text
CS50x_Final_Project/
├── app.py                  # Main Flask application and routing
├── helpers.py              # Utility functions (EcoQI math, apology, auth decorators)
├── automation.py           # Script to generate CSV files from the obtained PDFs
├── init_db.py              # Script to build aqi.db from CSVs
├── aqi.db                  # SQLite3 database (generated for 2025)
├── requirements.txt        # Python dependencies
├── static/
│   ├── favicon files       # favicon
│   ├── style.css           # Custom Glacier theme CSS overrides
│   └── script.js           # Single script to avoid inline scripts
└── templates/
    ├── layout.html         # Base template with Navbar and Theme switcher
    ├── login.html          # Username and password (for security while personalising database)
    ├── index.html          # Leaderboard homepage
    ├── city.html           # Individual city details
    ├── rank.html           # Personalization questionnaire
    ├── results.html        # Displaying personalised database
    ├── compare.html        # City comparison tool
    ├── methodology.html    # Documentation of the EcoQI thought process
    └── apology.html        # CS50 error renderer
```

---
## EcoQI Calculation:
*   if aqi <= 50:
        score = 100 - (aqi * 0.4)
*   elif aqi <= 100:
        score = 80 - ((aqi - 50) * 0.6)
*   elif aqi <= 200:
        score = 50 - ((aqi - 100) * 0.35)
*   elif aqi <= 300:
        score = 15 - ((aqi - 200) * 0.1)
*   elif aqi <= 400:
        score = max(5.0, 5 - ((aqi - 300) * 0.03))
*   else:
        score = max(0.0, 2 - ((aqi - 400) * 0.005))
* **Personalisation calculations:**\
if asthma == "yes":\
    score *= 1.2\
if outdoors == "yes":\
    score *= 1.1\
if children == "yes":\
    score *= 1.3\
if industrial == "yes":\
    score *= 1.15

## 4. Technologies Used
* **Backend:** Python, Flask, SQLite3
* **Frontend:** HTML5, CSS3, JavaScript (Vanilla), Bootstrap 5
* **Libraries/APIs/Tools:** Werkzeug (Security), Jinja

## 5. How to Run Locally

For deployment or sessions that must survive restarts, set a strong `FLASK_SECRET_KEY` environment variable. If it is omitted, the app uses an ephemeral key for local development.


1. Install dependencies: `pip install -r requirements.txt`
2. Start the Flask server: `flask run`
3. Open a web browser and navigate to `http://127.0.0.1:5000`
