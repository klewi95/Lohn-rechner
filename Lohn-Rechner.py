import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date

# -----------------------------------------------------------------------------
#  Optionale Bibliothek *holidays* für dynamische Feiertage (NRW)
# -----------------------------------------------------------------------------
try:
    import holidays  # pip install holidays
except ImportError:
    holidays = None  # Fallback, falls das Paket nicht installiert ist

# -----------------------------------------------------------------------------
#  Konstante Werte
# -----------------------------------------------------------------------------
MINDESTLOHN = 12.82  # €/h (2025)
MINIJOB_GRENZE = 556.0  # € pro Monat

RATES = {
    "rentenversicherung_minijob": 0.036,
    "sf_zuschlag_rate": 0.30,            # 30 % Sonntag/Feiertag (steuerfrei)
    "nacht_zuschlag_rate": 0.25,         # 25 % Nacht (steuerfrei)
    "pauschale_abzuege_ueber_minijob": 0.30,  # 30 % Pauschalabzug oberhalb Grenze
}

MONATE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]

# -----------------------------------------------------------------------------
#  Fallback‑Feiertage NRW für 2025 (falls *holidays* fehlt)
# -----------------------------------------------------------------------------
_FALLBACK_FEIERTAGE_2025_NRW = {
    (1, 1): "Neujahr",
    (4, 18): "Karfreitag",
    (4, 21): "Ostermontag",
    (5, 1): "Tag der Arbeit",
    (5, 29): "Christi Himmelfahrt",
    (6, 9): "Pfingstmontag",
    (6, 19): "Fronleichnam",
    (10, 3): "Tag der Deutschen Einheit",
    (11, 1): "Allerheiligen",
    (12, 25): "1. Weihnachtstag",
    (12, 26): "2. Weihnachtstag",
}


def get_feiertage_nrw(year: int) -> dict[tuple[int, int], str]:
    """Liefert NRW‑Feiertage als Dict {(Monat, Tag): Name} für *year*."""
    if holidays is not None:
        try:
            feiertage = holidays.Germany(prov="NW", years=[year])
            return {(d.month, d.day): name for d, name in feiertage.items()}
        except Exception as err:
            st.warning(f"Feiertage konnten nicht geladen werden: {err}")
    # Fallback nur für 2025, sonst leer
    if year == 2025:
        return _FALLBACK_FEIERTAGE_2025_NRW
    return {}

# -----------------------------------------------------------------------------
#  Hilfsfunktionen
# -----------------------------------------------------------------------------

def get_status_color(p: float) -> str:
    return "🔴" if p > 100 else "🟡" if p > 85 else "🟢"


def thermometer_html(p: float) -> str:
    color = "red" if p > 100 else "orange" if p > 85 else "green"
    width = min(100, p)
    return (
        f"<div style='width:100%;background:#f0f0f0;border-radius:10px;margin:10px 0;'>"
        f"<div style='width:{width}%;height:30px;background:{color};border-radius:10px;transition:width .5s'></div>"
        f"<div style='text-align:center;margin-top:-25px;color:#fff;font-weight:bold'>{p:.1f}%</div>"
        "</div>"
    )


def month_calendar_html(year: int, month: int, feiertage: dict) -> str:
    cal = calendar.monthcalendar(year, month)
    month_name = MONATE[month - 1]
    today = date.today()

    styles = (
        "<style>.calendar{width:100%;border-collapse:collapse;font-family:Arial}"
        ".calendar th{background:#f8f9fa;padding:10px;border:1px solid #dee2e6}"
        ".calendar td{padding:10px;text-align:center;border:1px solid #dee2e6}"
        ".holiday{background:#ffebee;color:#c62828;font-weight:bold}"
        ".today{background:#e3f2fd;font-weight:bold}"
        ".month-title{font-size:1.2em;font-weight:bold;margin-bottom:10px;text-align:center}</style>"
    )

    html = f"{styles}<div class='month-title'>{month_name} {year}</div><table class='calendar'>"
    html += "<tr><th>Mo</th><th>Di</th><th>Mi</th><th>Do</th><th>Fr</th><th>Sa</th><th>So</th></tr>"

    for week in cal:
        html += "<tr>"
        for day in week:
            if day == 0:
                html += "<td></td>"
            else:
                is_holiday = (month, day) in feiertage
                holiday_name = feiertage.get((month, day), "")
                is_today = (day == today.day and month == today.month and year == today.year)
                cls = "holiday" if is_holiday else "today" if is_today else ""
                title_attr = f" title='{holiday_name}'" if is_holiday else ""
                html += f"<td class='{cls}'{title_attr}>{day}</td>"
        html += "</tr>"
    html += "</table>"
    return html


def calculate_salary(grundlohn: float, stunden: float,
                     sf_zuschlag: bool, sf_stunden: float,
                     nacht_zuschlag: bool, nacht_stunden: float) -> dict:
    brutto_grundlohn_stunden = grundlohn * stunden
    brutto_grundlohn_fuer_grenze = brutto_grundlohn_stunden

    zuschlag_summe = 0.0
    if sf_zuschlag:
        zuschlag_summe += grundlohn * min(sf_stunden, stunden) * RATES["sf_zuschlag_rate"]
    if nacht_zuschlag:
        zuschlag_summe += grundlohn * min(nacht_stunden, stunden) * RATES["nacht_zuschlag_rate"]

    brutto_gesamt = brutto_grundlohn_fuer_grenze + zuschlag_summe

    if brutto_grundlohn_fuer_grenze <= MINIJOB_GRENZE:
        rv_abzug = brutto_grundlohn_fuer_grenze * RATES["rentenversicherung_minijob"]
        abzuege = rv_abzug
        pausch_abzug = 0.0
    else:
        rv_abzug = 0.0
        pausch_abzug = brutto_grundlohn_fuer_grenze * RATES["pauschale_abzuege_ueber_minijob"]
        abzuege = pausch_abzug

    netto = brutto_gesamt - abzuege

    freibetrag_rest = max(0, MINIJOB_GRENZE - brutto_grundlohn_fuer_grenze)
    rest_stunden = int(freibetrag_rest / grundlohn) if grundlohn else 0

    return {
        "brutto_grundlohn_stunden": brutto_grundlohn_stunden,
        "brutto_grundlohn_fuer_grenze": brutto_grundlohn_fuer_grenze,
        "zuschlag_summe": zuschlag_summe,
        "brutto_gesamt": brutto_gesamt,
        "netto": netto,
        "rentenversicherung_abzug": rv_abzug,
        "pauschale_abzuege": pausch_abzug,
        "gesamte_abzuege": abzuege,
        "freibetrag_rest": freibetrag_rest,
        "rest_stunden": rest_stunden,
    }

# -----------------------------------------------------------------------------
#  Streamlit‑App
# -----------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="Gehaltsrechner 2025", layout="wide")
    st.title("💰 Gehaltsrechner mit Zuschlägen 2025")

    # ---------------- Session‑State -------------------------------------------
    if "monthly_data" not in st.session_state:
        st.session_state.monthly_data = {
            m: {"grundlohn": MIN}
        }
