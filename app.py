import os
from flask import Flask, render_template, request, redirect, session, flash, g, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

from helpers import apology, login_required, calculate_ecoqi, get_grade, get_grade_color, SEASON_MONTHS

app = Flask(__name__)
# A secret key to help in packet encasing
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or os.urandom(32)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect("aqi.db")
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Custom Jinja filter to get grade colors in templates
@app.context_processor
def utility_processor():
    return dict(get_grade=get_grade, get_grade_color=get_grade_color)

@app.route("/")
def index():
    db = get_db()
    cursor = db.cursor()
    # Get leaderboard: average AQI by city
    cursor.execute('''SELECT c.id, c.name, c.state, ROUND(AVG(r.aqi), 1) as avg_aqi FROM cities c
        JOIN aqi_readings r ON c.id = r.city_id
        GROUP BY c.id
        ORDER BY avg_aqi ASC''')
    raw_cities = cursor.fetchall()

    cities = []
    for row in raw_cities:
        ecoqi = calculate_ecoqi(row['avg_aqi'])
        grade = get_grade(ecoqi)
        cities.append({
            'id': row['id'], 'name': row['name'], 'state': row['state'],
            'avg_aqi': row['avg_aqi'], 'ecoqi': ecoqi, 'grade': grade})

    # Re-sort by ecoqi descending
    cities.sort(key=lambda x: x['ecoqi'], reverse=True)

    return render_template("index.html", cities=cities)

@app.route("/city/<int:city_id>")
def city(city_id):
    db = get_db()
    cursor = db.cursor()

    # Get city details
    cursor.execute('SELECT * FROM cities WHERE id = ?', (city_id,))
    city = cursor.fetchone()

    if not city:
        return apology("City not found", 404)

    # Get readings
    cursor.execute('''SELECT date, aqi, prominent_pollutant, category FROM aqi_readings
        WHERE city_id = ?
        ORDER BY date ASC''', (city_id,))
    readings = cursor.fetchall()

    if not readings:
        return apology("No readings found for this city", 404)

    # Calculate stats
    total_aqi = sum(r['aqi'] for r in readings)
    avg_aqi = round(total_aqi / len(readings), 1)
    ecoqi = calculate_ecoqi(avg_aqi)
    grade = get_grade(ecoqi)

    best_aqi = min(r['aqi'] for r in readings)
    worst_aqi = max(r['aqi'] for r in readings)

    # Find most common pollutant
    pollutants = {}
    categories = {'Good': 0, 'Satisfactory': 0, 'Moderate': 0, 'Poor': 0, 'Very Poor': 0, 'Severe': 0}

    for r in readings:
        p = r['prominent_pollutant']
        if p and p != 'None':
            pollutants[p] = pollutants.get(p, 0) + 1

        cat = r['category']
        if cat in categories:
            categories[cat] += 1

    most_common_pollutant = "N/A"
    if pollutants:
        most_common_pollutant = max(pollutants, key=pollutants.get)

    stats = {
        'avg_aqi': avg_aqi,
        'ecoqi': ecoqi,
        'grade': grade,
        'best_aqi': best_aqi,
        'worst_aqi': worst_aqi,
        'total_readings': len(readings),
        'most_common_pollutant': most_common_pollutant
    }

    return render_template("city.html", city=city, readings=readings, stats=stats, categories=categories)

@app.route("/rank", methods=["GET", "POST"])
@login_required
def rank():
    if request.method == "POST":
        asthma = request.form.get("asthma")
        outdoors = request.form.get("outdoors")
        children = request.form.get("children")
        industrial = request.form.get("industrial")
        season = request.form.get("season")

        if not all([asthma, outdoors, children, industrial, season]):
            return apology("Must answer all questions", 400)

        # Standard un-filtered algorithm if they just submit here.
        # But we encourage them to use /rank/season for actual filtering now.
        db = get_db()
        cursor = db.cursor()

        # Get baseline averages
        months = SEASON_MONTHS[season]
        placeholders = ",".join("?" * len(months))
        query = f"""
            SELECT c.id, c.name, ROUND(AVG(r.aqi),1) AS avg_aqi
            FROM cities c
            JOIN aqi_readings r ON c.id = r.city_id
            WHERE substr(r.date,6,2) IN ({placeholders})
            GROUP BY c.id"""
        cursor.execute(query, months)
        baseline = cursor.fetchall()

        # Apply multipliers
        ranked_cities = []
        for row in baseline:
            score = float(row['avg_aqi'])

            if asthma == "yes":
                score *= 1.2
            if outdoors == "yes":
                score *= 1.1
            if children == "yes":
                score *= 1.3
            if industrial == "yes":
                score *= 1.15

            ecoqi = calculate_ecoqi(score)
            ranked_cities.append({"id": row['id'], "name": row['name'], "score": round(score, 1), "ecoqi": ecoqi})

        if session.get("user_id"):
            cursor.execute('''INSERT INTO user_responses (user_id, asthma, outdoors, children, industrial, season)
                VALUES (?, ?, ?, ?, ?, ?)''', (session["user_id"], asthma, outdoors, children, industrial, season))
            db.commit()
            ranked_cities.sort(key=lambda city: city["score"])

        return render_template("results.html", cities=ranked_cities[:50], season_name=season)

    else:
        return render_template("rank.html")

@app.route("/compare", methods=["GET", "POST"])
@login_required
def compare():
    db = get_db()
    cursor = db.cursor()

    # Get all cities for dropdowns
    cursor.execute('SELECT id, name FROM cities ORDER BY name')
    all_cities = cursor.fetchall()

    if request.method == "POST":
        city1_id = request.form.get("city1")
        city2_id = request.form.get("city2")

        if not city1_id or not city2_id:
            return apology("Must select two cities", 400)

        if city1_id == city2_id:
            return apology("Please select two different cities", 400)

        # Get city details
        cursor.execute('SELECT * FROM cities WHERE id = ?', (city1_id,))
        city1 = cursor.fetchone()
        cursor.execute('SELECT * FROM cities WHERE id = ?', (city2_id,))
        city2 = cursor.fetchone()

        # Get averages
        cursor.execute('SELECT ROUND(AVG(aqi), 1) as avg FROM aqi_readings WHERE city_id = ?', (city1_id,))
        city1_avg = cursor.fetchone()['avg']
        cursor.execute('SELECT ROUND(AVG(aqi), 1) as avg FROM aqi_readings WHERE city_id = ?', (city2_id,))
        city2_avg = cursor.fetchone()['avg']

        if city1_avg is None or city2_avg is None:
            return apology("Insufficient data for comparison", 404)

        city1_ecoqi = calculate_ecoqi(city1_avg)
        city2_ecoqi = calculate_ecoqi(city2_avg)

        return render_template("compare.html",
                               all_cities=all_cities,
                               city1=city1, city2=city2,
                               city1_avg=city1_avg, city2_avg=city2_avg,
                               city1_ecoqi=city1_ecoqi, city2_ecoqi=city2_ecoqi,
                               city1_grade=get_grade(city1_ecoqi), city2_grade=get_grade(city2_ecoqi))
    else:
        return render_template("compare.html", all_cities=all_cities)

@app.route("/methodology")
@login_required
def methodology():
    return render_template("methodology.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return apology("Must provide username and password", 403)

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            return apology("Invalid username and/or password", 403)

        session["user_id"] = user["id"]
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("Must provide username", 400)
        elif not password or password != confirmation:
            return apology("Invalid password or passwords do not match", 400)

        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                           (username, generate_password_hash(password)))
            db.commit()
        except sqlite3.IntegrityError:
            return apology("Username already exists", 400)

        # Log them in automatically
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        session["user_id"] = user["id"]

        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
