from functools import wraps
from flask import redirect, render_template, session

SEASON_MONTHS = {
    "Winter": ["01", "02"],
    "Summer": ["03", "04", "05"],
    "Monsoon": ["06", "07", "08", "09"],
    "Post-Monsoon": ["10", "11", "12"],
    "Any": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
}

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.
        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code

def login_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def calculate_ecoqi(aqi):
    """
    Calculate EcoQI based on piecewise air score function.
    Maps CPCB AQI (0-500+) into a 0-100 scale (100 is best).
    """
    if aqi <= 50:
        score = 100 - (aqi * 0.4)
    elif aqi <= 100:
        score = 80 - ((aqi - 50) * 0.6)
    elif aqi <= 200:
        score = 50 - ((aqi - 100) * 0.35)
    elif aqi <= 300:
        score = 15 - ((aqi - 200) * 0.1)
    elif aqi <= 400:
        score = max(5.0, 5 - ((aqi - 300) * 0.03))
    else:
        score = max(0.0, 2 - ((aqi - 400) * 0.005))

    return round(score, 1)

def get_grade(ecoqi):
    """Return letter grade based on EcoQI."""
    if ecoqi >= 95:
        return "A+"
    if ecoqi >= 85:
        return "A"
    if ecoqi >= 70:
        return "B"
    if ecoqi >= 55:
        return "C"
    if ecoqi >= 40:
        return "D"
    return "F"

def get_grade_color(grade):
    """Return Bootstrap badge color class based on letter grade."""
    colors = {
        "A+": "bg-success",
        "A": "bg-success text-dark",
        "B": "bg-info text-dark",
        "C": "bg-warning text-dark",
        "D": "bg-danger",
        "F": "bg-dark text-white"
    }
    # Adjusting to match the previous AQI colors roughly to standard Bootstrap
    if grade in ["A+", "A"]:
        return "bg-success"
    elif grade == "B":
        return "bg-warning text-dark"
    elif grade == "C":
        return "bg-warning text-dark" # No orange in standard bootstrap, warning is closest
    elif grade == "D":
        return "bg-danger"
    else:
        return "bg-dark text-white"
