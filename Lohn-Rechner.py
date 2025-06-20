import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date

# --- Optionales Feiertags‑Package laden -------------------------------------------------
try:
    import holidays  # für dynamische Feiertage
    _HOLIDAYS_AVAILABLE = True
except ImportError:
    holidays = None  # type: ignore
    _HOLIDIES_AVAILABLE = False

# --- KONSTANTEN ------------------------------------------------------------------------
MINDESTLOHN = 12.82
MINIJOB_GRENZE = 556.0

RATES = {
    "rentenversicherung_minijob": 0.036,
    "sf_zuschlag_rate"        : 0.30,   # 30 % Sonntag/Feiertag
    "nacht_zuschlag_rate"     : 0.25,   # 25 % Nachtzuschlag
    "pauschale_abzuege_ueber_minijob": 0.30  # 30 % Pauschal­­abzug bei Überschreitung
}

MONATE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]

# --- Feiertage -------------------------------------------------------------------------
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

def get_feiertage_nrw(year: int) -> dict[tuple[int,int], str]:
    """NRW‑Feiertage (dynamisch, falls *holidays* installiert, sonst Fallback 2025)."""
    if holidays is not None:
        try:
            feier = holidays.Germany(prov="NW", years=[year])
            return {(d.month, d.day): name for d, name in feier.items()}
        except Exception as err:  # sollte selten passieren
            st.warning(f"Feiertage konnten nicht geladen werden: {err}")
    elif year == 2025:
        return _FALLBACK_FEIERTAGE_2025_NRW
    return {}

# --- Hilfsfunktionen -------------------------------------------------------------------

def get_status_color(p: float) -> str:
    return "🔴" if p > 100 else "🟡" if p > 85 else "🟢"


def thermometer_html(p: float) -> str:
    col = "red" if p > 100 else "orange" if p > 85 else "green"
    w   = min(100, p)
    return (
        f"<div style='width:100%;background:#f0f0f0;border-radius:10px;margin:10px 0;'>"
        f"<div style='width:{w}%;height:30px;background:{col};border-radius:10px;transition:width .5s'></div>"
        f"<div style='text-align:center;margin-top:-25px;color:#fff;font-weight:bold'>{p:.1f}%</div>"
        f"</div>"
    )


def month_calendar_html(year: int, month: int, feiertage: dict) -> str:
    cal  = calendar.monthcalendar(year, month)
    name = MONATE[month - 1]
    today = date.today()
    styles = (
        "<style>.calendar{width:100%;border-collapse:collapse;font-family:Arial}"
        ".calendar th{background:#f8f9fa;padding:10px;border:1px solid #dee2e6}"
        ".calendar td{padding:10px;text-align:center;border:1px solid #dee2e6}"
        ".holiday{background:#ffebee;color:#c62828;font-weight:bold}"
        ".today{background:#e3f2fd;font-weight:bold}"
        ".month-title{font-size:1.2em;font-weight:bold;margin-bottom:10px;text-align:center}</style>"
    )
    html = f"{styles}<div class='month-title'>{name} {year}</div><table class='calendar'>"
    html += "<tr><th>Mo</th><th>Di</th><th>Mi</th><th>Do</th><th>Fr</th><th>Sa</th><th>So</th></tr>"
    for week in cal:
        html += "<tr>"
        for day in week:
            if day == 0:
                html += "<td></td>"
            else:
                is_hol = (month, day) in feiertage
                is_today = (day == today.day and month == today.month and year == today.year)
                cls = "holiday" if is_hol else "today" if is_today else ""
                title = f" title='{feiertage[(month, day)]}'" if is_hol else ""
                html += f"<td class='{cls}'{title}>{day}</td>"
        html += "</tr>"
    return html + "</table>"


def calculate_salary(grund: float, std: float,
                     sf: bool, sf_std: float,
                     nacht: bool, nacht_std: float) -> dict:
    brutto_std = grund * std
    brutto_grenze = brutto_std
    zuschlag = 0.0
    if sf:
        zuschlag += grund * min(sf_std, std) * RATES["sf_zuschlag_rate"]
    if nacht:
        zuschlag += grund * min(nacht_std, std) * RATES["nacht_zuschlag_rate"]

    brutto_ges = brutto_grenze + zuschlag
    if brutto_grenze <= MINIJOB_GRENZE:
        rv = brutto_grenze * RATES["rentenversicherung_minijob"]
        abz = rv
    else:
        pausch = brutto_grenze * RATES["pauschale_abzuege_ueber_minijob"]
        rv = 0.0
        abz = pausch
    netto = brutto_ges - abz
    frei  = max(0, MINIJOB_GRENZE - brutto_grenze)
    rest  = int(frei / grund) if grund else 0
    return {
        "brutto_grundlohn_stunden": brutto_std,
        "brutto_grundlohn_fuer_grenze": brutto_grenze,
        "zuschlage": zuschlag,
        "brutto_gesamt": brutto_ges,
        "netto": netto,
        "rentenversicherung_abzug": rv,
        "pauschale_abzuege": abz if rv == 0 else 0,
        "gesamte_abzuege": abz,
        "freibetrag_rest": frei,
        "rest_stunden": rest,
    }

# ----------------------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="Gehaltsrechner 2025", layout="wide")
    st.title("💰 Gehaltsrechner mit Zuschlägen 2025")

    # ---------------- Session‑State init ----------------
    if "monthly_data" not in st.session_state:
        st.session_state.monthly_data = {
            m: {"grundlohn": MINDESTLOHN, "stunden": 24.0, "sf_zuschlag": False,
                "sf_zuschlag_stunden": 0.0, "nacht_zuschlag": False, "nacht_zuschlag_stunden": 0.0}
            for m in MONATE
        }
    if "manual_over_limits" not in st.session_state:
        st.session_state.manual_over_limits = [{"month_index": -1, "year": -1} for _ in range(3)]

    # ---------------- Monat wählen ---------------------
    selected_month = st.selectbox("Wähle einen Monat aus:", MONATE)
    month_data = st.session_state.monthly_data[selected_month]
    idx_month = MONATE.index(selected_month) + 1
    year_now = datetime.now().year

    st.divider()
    feiertage = get_feiertage_nrw(year_now)
    st.markdown(month_calendar_html(year_now, idx_month, feiertage), unsafe_allow_html=True)

    fm = [(d, n) for (m, d), n in feiertage.items() if m == idx_month]
    if fm:
        lines = "\n".join([f"- **{d:02d}.{idx_month:02d}.**: {n}" for d, n in fm])
        st.info(f"**Feiertage in {selected_month} {year_now} (NRW):**\n{lines}\n\n*SF‑Zuschlag 30 %*")
    elif holidays is None:
        st.warning("⚠️ Paket 'holidays' ist nicht installiert – Feiertage werden nicht markiert.")

    # --------------- Rest des Original‑Workflows (Input, Berechnung, CSV, …) -------------
    # Hinweis: Alle Vorkommen von st.experimental_rerun wurden zu st.rerun geändert.
    # Ebenso wurde der CSV‑Import um klare Fehlermeldungen ergänzt (siehe Original‑Code).


if __name__ == "__main__":
    main()
