# Weather App (Flask + Tailwind)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## Notes

- The UI expects latitude/longitude coordinates and fetches data from api.weather.gov.
- Weather.gov requires a User-Agent header; set one with:

```bash
export WEATHER_GOV_USER_AGENT="weather-app (you@example.com)"
```
