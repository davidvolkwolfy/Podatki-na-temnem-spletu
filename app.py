import logging
import os
from urllib.parse import quote

import requests
from flask import Flask, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

# --- Konfiguracija ---------------------------------------------------------

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    # Glasno padi ob zagonu, namesto da vsaka poizvedba tiho odpove.
    raise RuntimeError(
        "Manjka okoljska spremenljivka API_KEY (LeakCheck Pro API v2 ključ)."
    )

LEAKCHECK_URL = "https://leakcheck.io/api/v2/query/{query}"
REQUEST_TIMEOUT = 10  # sekund

logging.basicConfig(level=logging.INFO)
# Pomembno: nikoli ne logiramo vnesenega e-naslova (zasebnost).
logger = logging.getLogger("darkweb-checker")

app = Flask(__name__)

# Render je reverse proxy — brez ProxyFix vsi zahtevki izgledajo kot isti IP,
# kar bi pokvarilo rate limiting (in logiko po IP-ju nasploh).
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

# Rate limiting: brani pred zlorabo (množično preverjanje tujih naslovov,
# praznjenje LeakCheck kvote). Za produkcijo priporočen Redis storage_uri,
# da števci preživijo restarte/cold-starte na Renderju.
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["100 per day"],
    storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
)


# --- Pomožne funkcije ------------------------------------------------------

def check_email(email):
    """Poizvedba proti LeakCheck Pro API v2.

    Vrne (results, error), kjer je results:
      - None   ob napaki,
      - []     če ni najdenih vdorov,
      - seznam slovarjev z opisom vsakega vira sicer.
    """
    headers = {"Accept": "application/json", "X-API-Key": API_KEY}
    url = LEAKCHECK_URL.format(query=quote(email, safe=""))

    try:
        res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.Timeout:
        logger.warning("LeakCheck timeout")
        return None, "Storitev se trenutno ne odziva. Poskusite čez nekaj minut."
    except requests.RequestException:
        logger.exception("LeakCheck request failed")
        return None, "Storitev trenutno ni dosegljiva. Poskusite pozneje."

    if res.status_code == 400:
        # Npr. neveljaven format e-naslova — uporabniku razumljivo sporočilo.
        return None, "Vnesite veljaven e-poštni naslov."
    if res.status_code == 429:
        return None, "Preveč poizvedb. Počakajte trenutek in poskusite znova."
    if res.status_code in (401, 403):
        # Težava na naši strani (ključ/kvota) — ne razkrivamo podrobnosti.
        logger.error("LeakCheck auth/quota problem: HTTP %s", res.status_code)
        return None, "Storitev trenutno ni na voljo. Poskusite pozneje."
    if res.status_code != 200:
        logger.error("LeakCheck unexpected status: HTTP %s", res.status_code)
        return None, "Prišlo je do napake. Poskusite znova."

    try:
        data = res.json()
    except ValueError:
        logger.error("LeakCheck returned non-JSON response")
        return None, "Prišlo je do napake. Poskusite znova."

    if not data.get("success"):
        return None, "Prišlo je do napake. Poskusite znova."

    if not data.get("found"):
        return [], None

    # Preslikamo surovi odgovor v predlogo-prijazno obliko.
    results = []
    for row in data.get("result", []):
        source = row.get("source") or {}
        results.append(
            {
                "name": source.get("name", "Neznan vir"),
                "date": source.get("breach_date") or row.get("collected") or "—",
                "fields": row.get("fields", []),
                "unverified": bool(source.get("unverified")),
            }
        )
    return results, None


# --- Poti ------------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def index():
    results = None
    error = None

    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        if email:
            results, error = check_email(email)

    return render_template("index.html", results=results, error=error)


@app.route("/faq")
def faq():
    return render_template("faq.html")


@app.route("/healthz")
def healthz():
    # Lahka točka za keep-alive ping (npr. cron-job.org proti cold-startu).
    return "ok", 200


@app.errorhandler(429)
def ratelimit_handler(e):
    return render_template(
        "index.html",
        results=None,
        error="Preveč poizvedb. Počakajte minuto in poskusite znova.",
    ), 429


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
