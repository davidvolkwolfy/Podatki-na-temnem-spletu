# 🔍 Dark Web Checker

Spletna aplikacija za preverjanje, ali je e-poštni naslov del znanih vdorov podatkov in objavljen na temnem spletu. Poganja jo [LeakCheck.io](https://leakcheck.io) Pro API v2.

Razvito v **[SRC d.o.o.](https://src.si)** kot javno ozaveščevalno orodje o varnosti prijavnih podatkov.

## Funkcionalnosti

- Preverjanje e-poštnega naslova proti bazi z več milijardami razkritih zapisov
- Prikaz vira vdora, datuma in vrste razkritih podatkov (geslo, uporabniško ime, telefon ipd.)
- Stopnja ogroženosti glede na število najdenih virov
- Izvoz rezultatov in varnostnega kontrolnega seznama v PDF
- Stran s pogostimi vprašanji (FAQ)
- Odziven, mobilnim napravam prilagojen vmesnik (slovenski jezik)

## Varnost in zasebnost

- E-poštni naslov se posreduje izključno storitvi LeakCheck.io za preverjanje in se **ne shranjuje** v lastno bazo
- Poizvedbe potekajo prek POST (naslov ne konča v strežniških dnevnikih URL-jev)
- Omejevanje hitrosti (rate limiting) preprečuje množično preverjanje in zlorabo API kvote
- Vhodni podatki so sanitizirani pred posredovanjem zunanjemu API-ju
- API ključ se bere iz okoljske spremenljivke, nikoli iz kode

## Tehnološki sklad

- **Backend:** Python 3.8+, Flask
- **Zunanji API:** LeakCheck.io Pro API v2
- **Frontend:** HTML, CSS, JavaScript (CSS in JS sta vgrajena v predloge)
- **Knjižnice (CDN):** jsPDF, animate.css
- **Streženje:** Gunicorn

## Lokalni zagon

```bash
# 1. Namestitev odvisnosti
pip install -r requirements.txt

# 2. Nastavitev API ključa
export API_KEY="vas_leakcheck_api_kljuc"

# 3. Zagon
gunicorn app:app
```

Aplikacija je nato dosegljiva na `http://localhost:8000`.

## Namestitev na Render

Servis mora biti tipa **Web Service** (ne Static Site — sicer se Jinja predloge ne obdelajo):

| Nastavitev | Vrednost |
| --- | --- |
| Environment | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app` |
| Environment Variable | `API_KEY` = vaš LeakCheck ključ |

Neobvezno: `RATELIMIT_STORAGE_URI` (npr. Redis) za trajno omejevanje hitrosti med ponovnimi zagoni.

## Struktura projekta

```
.
├── app.py                 # Flask aplikacija in logika poizvedbe
├── requirements.txt       # Python odvisnosti
├── templates/
│   ├── index.html         # Glavna stran (CSS + JS vgrajena)
│   └── faq.html           # Pogosta vprašanja
└── static/
    └── logo.png           # Logotip SRC d.o.o.
```

## Opozorilo

To orodje je namenjeno ozaveščanju in preverjanju lastnih podatkov. Uporabljajte ga odgovorno in v skladu s pogoji uporabe LeakCheck.io.

---

© 2026 Dark Web Credential Checker · Razvito v [SRC d.o.o.](https://src.si)
