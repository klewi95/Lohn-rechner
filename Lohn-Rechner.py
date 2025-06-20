import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date
import holidays  # Neues Package für Feiertage

# --- KONSTANTEN ---
MINDESTLOHN = 12.82
MINIJOB_GRENZE = 556.0

# Steuersätze und Zuschlagsraten
RATES = {
    "rentenversicherung_minijob": 0.036,
    "sf_zuschlag_rate": 0.30,  # 30% SF-Zuschlag
    "nacht_zuschlag_rate": 0.25,  # 25% Nacht-Zuschlag
    "pauschale_abzuege_ueber_minijob": 0.30  # 30% pauschale Abzüge bei Überschreitung
}

MONATE = [
    'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
    'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'
]

# --- HILFSFUNKTIONEN ---

def get_feiertage_nrw(year: int):
    """Erstellt ein Dict der NRW‑Feiertage für das angegebene Jahr."""
    feiertage = holidays.Germany(prov='NW', years=[year])
    return {(d.month, d.day): name for d, name in feiertage.items()}


def get_status_color(prozent: float) -> str:
    if prozent > 100:
        return "🔴"
    elif prozent > 85:
        return "🟡"
    else:
        return "🟢"


def get_thermometer_html(prozent: float) -> str:
    color = "red" if prozent > 100 else "orange" if prozent > 85 else "green"
    width = min(100, prozent)
    return f"""
        <div style="width:100%; background-color:#f0f0f0; border-radius:10px; margin:10px 0;">
            <div style="width:{width}%; height:30px; background-color:{color}; 
                 border-radius:10px; transition:width 0.5s;">
            </div>
            <div style="text-align:center; margin-top:-25px; color:white; font-weight:bold;">
                {prozent:.1f}%
            </div>
        </div>
    """


def get_month_calendar_html(year: int, month: int, feiertage: dict) -> str:
    cal = calendar.monthcalendar(year, month)
    month_name = MONATE[month-1]

    styles = """
    <style>
        .calendar {width: 100%; border-collapse: collapse; font-family: Arial, sans-serif;}
        .calendar th {background-color: #f8f9fa; padding: 10px; text-align: center; border: 1px solid #dee2e6;}
        .calendar td {padding: 10px; text-align: center; border: 1px solid #dee2e6;}
        .holiday {background-color: #ffebee; color: #c62828; font-weight: bold;}
        .today {background-color: #e3f2fd; font-weight: bold;}
        .month-title {font-size: 1.2em; font-weight: bold; margin-bottom: 10px; text-align: center;}
    </style>
    """

    html = f"{styles}<div class='month-title'>{month_name} {year}</div>"
    html += "<table class='calendar'>"
    html += "<tr><th>Mo</th><th>Di</th><th>Mi</th><th>Do</th><th>Fr</th><th>Sa</th><th>So</th></tr>"

    today = date.today()

    for week in cal:
        html += "<tr>"
        for day in week:
            if day == 0:
                html += "<td></td>"
            else:
                is_holiday = (month, day) in feiertage
                holiday_name = feiertage.get((month, day), '')

                is_today = (day == today.day and month == today.month and year == today.year)

                cell_class = 'holiday' if is_holiday else 'today' if is_today else ''
                title_attr = f" title='{holiday_name}'" if is_holiday else ''

                html += f"<td class='{cell_class}'{title_attr}>{day}</td>"
        html += "</tr>"
    html += "</table>"

    return html


def calculate_salary(grundlohn: float, stunden: float,
                     sf_zuschlag: bool, sf_zuschlag_stunden: float,
                     nacht_zuschlag: bool, nacht_zuschlag_stunden: float) -> dict:

    brutto_grundlohn_stunden = grundlohn * stunden
    brutto_grundlohn_fuer_grenze = brutto_grundlohn_stunden

    zuschlage = 0.0
    if sf_zuschlag:
        sf_stunden = min(sf_zuschlag_stunden, stunden)
        zuschlage += grundlohn * sf_stunden * RATES["sf_zuschlag_rate"]

    if nacht_zuschlag:
        nacht_stunden = min(nacht_zuschlag_stunden, stunden)
        zuschlage += grundlohn * nacht_stunden * RATES["nacht_zuschlag_rate"]

    brutto_gesamt = brutto_grundlohn_fuer_grenze + zuschlage

    rentenversicherung_abzug = 0.0
    pauschale_abzuege = 0.0

    if brutto_grundlohn_fuer_grenze <= MINIJOB_GRENZE:
        rentenversicherung_abzug = brutto_grundlohn_fuer_grenze * RATES["rentenversicherung_minijob"]
        gesamte_abzuege = rentenversicherung_abzug
    else:
        pauschale_abzuege = brutto_grundlohn_fuer_grenze * RATES["pauschale_abzuege_ueber_minijob"]
        gesamte_abzuege = pauschale_abzuege

    netto = brutto_gesamt - gesamte_abzuege

    freibetrag_rest = max(0, MINIJOB_GRENZE - brutto_grundlohn_fuer_grenze)
    rest_stunden = int(freibetrag_rest / grundlohn) if grundlohn > 0 else 0

    return {
        'brutto_grundlohn_stunden': brutto_grundlohn_stunden,
        'brutto_grundlohn_fuer_grenze': brutto_grundlohn_fuer_grenze,
        'zuschlage': zuschlage,
        'brutto_gesamt': brutto_gesamt,
        'netto': netto,
        'gesamte_abzuege': gesamte_abzuege,
        'rentenversicherung_abzug': rentenversicherung_abzug,
        'pauschale_abzuege': pauschale_abzuege,
        'freibetrag_rest': freibetrag_rest,
        'rest_stunden': rest_stunden
    }

# --- HAUPTTEIL DER STREAMLIT APP ---

def main():
    st.set_page_config(page_title="Gehaltsrechner 2025", layout="wide")
    st.title("💰 Gehaltsrechner mit Zuschlägen 2025")

    # Session‑State‑Initialisierung
    if 'monthly_data' not in st.session_state:
        st.session_state.monthly_data = {
            month: {
                'grundlohn': MINDESTLOHN,
                'stunden': 24.0,
                'sf_zuschlag': False,
                'sf_zuschlag_stunden': 0.0,
                'nacht_zuschlag': False,
                'nacht_zuschlag_stunden': 0.0
            } for month in MONATE
        }

    if 'manual_over_limits' not in st.session_state:
        st.session_state.manual_over_limits = [
            {'month_index': -1, 'year': -1},
            {'month_index': -1, 'year': -1},
            {'month_index': -1, 'year': -1}
        ]

    # Monat wählen
    selected_month = st.selectbox("Wähle einen Monat aus:", MONATE)
    month_data = st.session_state.monthly_data[selected_month]

    st.divider()

    # Kalender & Feiertage
    current_year = datetime.now().year
    month_index = MONATE.index(selected_month) + 1
    feiertage_nrw = get_feiertage_nrw(current_year)
    calendar_html = get_month_calendar_html(current_year, month_index, feiertage_nrw)
    st.markdown(calendar_html, unsafe_allow_html=True)

    feiertage_im_monat = [(day, name) for (m, day), name in feiertage_nrw.items() if m == month_index]
    if feiertage_im_monat:
        feiertage_text = "\n".join([f"- **{day:02d}.{month_index:02d}.**: {name}" for day, name in feiertage_im_monat])
        st.info(f"""
        **Feiertage in {selected_month} {current_year} (NRW):**
        {feiertage_text}

        *An gesetzlichen Feiertagen gilt der SF-Zuschlag (30%).*
        """)

    st.divider()

    # --- Rest des ursprünglichen Codes bleibt unverändert ---
    # [...] (wegen Kürze hier ausgelassen – es wurden nur folgende Stellen angepasst)

    # 1) Alle Vorkommen von st.experimental_rerun() wurden durch st.rerun() ersetzt.
    # 2) CSV‑Import – klarere Fehlermeldung, falls Spalten fehlen.

    # Beispielhafte Stelle im CSV‑Import‑Block:
    # if not all(col in df.columns for col in required_columns_monthly):
    #     missing = [col for col in required_columns_monthly if col not in df.columns]
    #     st.error(f"Fehler beim CSV‑Import. Folgende Spalten fehlen: {', '.join(missing)}")
    #     return

if __name__ == "__main__":
    main()
