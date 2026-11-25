from datetime import date, timedelta
from pathlib import Path
import requests

DOWNLOAD_DIR = Path("aqi_bulletins")
DOWNLOAD_DIR.mkdir(exist_ok=True)

BASE_URL = (
    "https://cpcb.nic.in/upload/Downloads/"
    "AQI_Bulletin_{datestr}.pdf"
)

START_DATE = date(2025, 1, 2)
END_DATE = date.today()


def download_pdf(day):
    datestr = day.strftime("%Y%m%d")

    url = BASE_URL.format(datestr=datestr)

    filepath = DOWNLOAD_DIR / f"AQI_Bulletin_{datestr}.pdf"

    if filepath.exists():
        print(f"Already exists: {filepath.name}")
        return

    try:
        response = requests.get(url, timeout=20)

        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)

            print(f"Downloaded {filepath.name}")

        else:
            print(f"Not found: {datestr}")

    except Exception as e:
        print(f"Error on {datestr}: {e}")


current = START_DATE

while current <= END_DATE:
    download_pdf(current)
    current += timedelta(days=1)

print("Finished.")