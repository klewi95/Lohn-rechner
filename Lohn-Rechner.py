import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date

# Konstanten müssen hier oben definiert sein, damit sie im gesamten Modul verfügbar sind.
MINDESTLOHN = 12.82
MINIJOB_GRENZE = 556.0
MONATE = [
    'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
    'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'
]

# Feiertage NRW 2025 mit genauen Daten
FEIERTAGE_NRW_2025 = {
    (1, 1): 'Neujahr',
    (4, 18): 'Karfreitag',
    (4, 21): 'Ostermontag',
    (5, 1): 'Tag der Arbeit',
    (5, 29): 'Christi Himmelfahrt',
    (6, 9): 'Pfingstmontag',
    (6, 19): 'Fronleichnam',
    (10, 3): 'Tag der Deutschen Einheit',
    (11, 1): 'Allerheiligen',
    (12, 25): '1. Weihnachtstag',
    (12, 26): '2. Weihnachtstag'
}

def get_status_color(prozent):
    """Gibt die Farbe basierend auf dem Prozentsatz zurück."""
    if prozent > 100:
        return "🔴"
    elif prozent > 85:
        return "🟡"
    else:
        return "🟢"

def get_thermometer_html(prozent):
    """Erstellt eine Thermometer-Anzeige als HTML."""
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

def get_month_calendar_html(year, month, feiertage):
    """Erstellt einen HTML-Kalender mit markierten Feiertagen."""
    cal = calendar.monthcalendar(year, month)
    month_name = MONATE[month-1]
    
    # Kalenderstile
    styles = """
    <style>
        .calendar {
            width: 100%;
            border-collapse: collapse;
            font-family: Arial, sans-serif;
        }
        .calendar th {
            background-color: #f8f9fa;
            padding: 10px;
            text-align: center;
            border: 1px solid #dee2e6;
        }
        .calendar td {
            padding: 10px;
            text-align: center;
            border: 1px solid #dee2e6;
        }
        .holiday {
            background-color: #ffebee;
            color: #c62828;
            font-weight: bold;
        }
        .today {
            background-color: #e3f2fd;
            font-weight: bold;
        }
        .month-title {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 10px;
            text-align: center;
        }
    </style>
    """
    
    # Kalender HTML
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
                # Prüfen ob Feiertag
                is_holiday = (month, day) in feiertage
                holiday_name = feiertage.get((month, day), '')
                
                # Prüfen ob heute
                is_today = (day == today.day and month == today.month and year == today.year)
                
                # Zellenklasse bestimmen
                cell_class = 'holiday' if is_holiday else 'today' if is_today else ''
                
                # Tooltip mit Feiertagsname
                title_attr = f" title='{holiday_name}'" if is_holiday else ''
                
                html += f"<td class='{cell_class}'{title_attr}>{day}</td>"
        html += "</tr>"
    html += "</table>"
    
    return html

def calculate_salary(grundlohn: float, stunden: float, 
                    sf_zuschlag: bool, sf_zuschlag_stunden: float,
                    nacht_zuschlag: bool, nacht_zuschlag_stunden: float) -> dict:
    """Berechnet das Gehalt mit allen Zuschlägen und Abzügen."""
    
    # Grundlohn berechnen (relevant für Minijob-Grenze)
    brutto_grundlohn = grundlohn * stunden
    
    # Zuschläge berechnen (steuerfrei)
    zuschlage = 0.0
    if sf_zuschlag:
        sf_stunden = min(sf_zuschlag_stunden, stunden)
        zuschlage += grundlohn * sf_stunden * 0.3  # 30% SF-Zuschlag
    if nacht_zuschlag:
        nacht_stunden = min(nacht_zuschlag_stunden, stunden)
        zuschlage += grundlohn * nacht_stunden * 0.25  # 25% Nacht-Zuschlag
        
    # Gesamtbrutto (mit Zuschlägen)
    brutto_gesamt = brutto_grundlohn + zuschlage
    
    # Abzüge berechnen
    rentenversicherung = brutto_grundlohn * 0.036  # 3,6% Rentenversicherung für Minijobs
    if brutto_grundlohn > MINIJOB_GRENZE:
        abzuge = brutto_grundlohn * 0.30
    else:
        abzuge = rentenversicherung
            
    netto = brutto_gesamt - abzuge
    
    freibetrag_rest = max(0, MINIJOB_GRENZE - brutto_grundlohn)
    rest_stunden = int(freibetrag_rest / grundlohn)
    
    return {
        'brutto_grundlohn': brutto_grundlohn,
        'zuschlage': zuschlage,
        'brutto_gesamt': brutto_gesamt,
        'netto': netto,
        'abzuge': abzuge,
        'rentenversicherung': rentenversicherung if brutto_grundlohn <= MINIJOB_GRENZE else 0.0,
        'freibetrag_rest': freibetrag_rest,
        'rest_stunden': rest_stunden
    }

def main():
    st.set_page_config(page_title="Gehaltsrechner 2025", layout="wide")
    st.title("Gehaltsrechner mit Zuschlägen 2025")
    
    # Initialisiere Session State für monatliche Daten
    if 'monthly_data' not in st.session_state:
        st.session_state.monthly_data = {
            month: {
                'grundlohn': MINDESTLOHN,
                'stunden': 24.0,
                'sf_zuschlag': True,
                'sf_zuschlag_stunden': 12.0,
                'nacht_zuschlag': False,
                'nacht_zuschlag_stunden': 0.0
            } for month in MONATE
        }
    
    selected_month = st.selectbox("Monat auswählen", MONATE)
    month_data = st.session_state.monthly_data[selected_month]
    
    # Kalender mit Feiertagen anzeigen
    month_index = MONATE.index(selected_month) + 1
    calendar_html = get_month_calendar_html(2025, month_index, FEIERTAGE_NRW_2025)
    st.markdown(calendar_html, unsafe_allow_html=True)
    
    # Feiertage des Monats anzeigen
    feiertage_im_monat = [(day, name) for (m, day), name in FEIERTAGE_NRW_2025.items() if m == month_index]
    if feiertage_im_monat:
        feiertage_text = "\n".join([f"- {day:02d}.{month_index:02d}.: {name}" for day, name in feiertage_im_monat])
        st.info(f"""
        **Feiertage in {selected_month} 2025 (NRW):**
        {feiertage_text}
        
        An Feiertagen gilt der SF-Zuschlag (30%).
        """)
    
    # Vorlagen für typische Szenarien
    template = st.selectbox(
        "Vorlage laden",
        ["Individuell", "6h/Woche (24h/Monat)", "8h/Woche (32h/Monat)", "10h/Woche (40h/Monat)"]
    )
    
    if template != "Individuell":
        if template == "6h/Woche (24h/Monat)":
            month_data['stunden'] = 24.0
        elif template == "8h/Woche (32h/Monat)":
            month_data['stunden'] = 32.0
        elif template == "10h/Woche (40h/Monat)":
            month_data['stunden'] = 40.0
    
    col1, col2 = st.columns(2)
    with col1:
        grundlohn = st.number_input(
            "Stundenlohn (€)",
            min_value=MINDESTLOHN,
            value=month_data['grundlohn'],
            step=0.5,
            format="%.2f"
        )
    with col2:
        stunden = st.number_input(
            "Stunden pro Monat",
            min_value=0.0,
            value=month_data['stunden'],
            step=1.0,
            format="%.1f"
        )
    
    st.subheader("Zuschläge (steuerfrei)")
    col1, col2 = st.columns(2)
    with col1:
        sf_zuschlag = st.checkbox("SF-Zuschlag (30%)", value=month_data['sf_zuschlag'])
    with col2:
        sf_zuschlag_stunden = st.number_input(
            "Stunden mit SF-Zuschlag",
            min_value=0.0,
            max_value=stunden,
            value=month_data['sf_zuschlag_stunden'],
            step=1.0,
            format="%.1f",
            disabled=not sf_zuschlag
        )
    
    col1, col2 = st.columns(2)
    with col1:
        nacht_zuschlag = st.checkbox("Nacht-Zuschlag (25%)", value=month_data['nacht_zuschlag'])
    with col2:
        nacht_zuschlag_stunden = st.number_input(
            "Stunden mit Nacht-Zuschlag",
            min_value=0.0,
            max_value=stunden,
            value=month_data['nacht_zuschlag_stunden'],
            step=1.0,
            format="%.1f",
            disabled=not nacht_zuschlag
        )
        
    st.session_state.monthly_data[selected_month] = {
        'grundlohn': grundlohn,
        'stunden': stunden,
        'sf_zuschlag': sf_zuschlag,
        'sf_zuschlag_stunden': sf_zuschlag_stunden,
        'nacht_zuschlag': nacht_zuschlag,
        'nacht_zuschlag_stunden': nacht_zuschlag_stunden
    }
    
    results = calculate_salary(
        grundlohn, stunden, 
        sf_zuschlag, sf_zuschlag_stunden,
        nacht_zuschlag, nacht_zuschlag_stunden
    )
    
    # Berechnung des Prozentsatzes und Status
    prozent_ausgeschoepft = (results['brutto_grundlohn'] / MINIJOB_GRENZE) * 100
    status_emoji = get_status_color(prozent_ausgeschoepft)
    
    # Thermometer-Anzeige
    st.subheader(f"Minijob-Grenze Status {status_emoji}")
    st.write(f"**{prozent_ausgeschoepft:.1f}%** der Minijob-Grenze ausgeschöpft")
    st.markdown(get_thermometer_html(prozent_ausgeschoepft), unsafe_allow_html=True)
    
    # Ergebnisse
    st.subheader("Monatsbeträge")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Brutto Grundlohn", f"{results['brutto_grundlohn']:.2f} €")
    with col2:
        st.metric("Steuerfreie Zuschläge", f"{results['zuschlage']:.2f} €")
    with col3:
        st.metric("Brutto gesamt", f"{results['brutto_gesamt']:.2f} €")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Netto", f"{results['netto']:.2f} €")
    with col2:
        st.metric("Noch bis Minijob-Grenze", f"{results['freibetrag_rest']:.2f} € ({results['rest_stunden']} Stunden)")
    
    if results['brutto_grundlohn'] > MINIJOB_GRENZE:
        st.error(f"""
        Minijob-Grenze überschritten!
        - Grundlohn: {results['brutto_grundlohn']:.2f} €
        - Grenze: {MINIJOB_GRENZE:.2f} €
        - Überschreitung: {(results['brutto_grundlohn'] - MINIJOB_GRENZE):.2f} €
        
        Die Zuschläge ({results['zuschlage']:.2f} €) sind steuerfrei und zählen nicht zur Minijob-Grenze!
        """)
    else:
        st.success(f"""
        Innerhalb der Minijob-Grenze ✓
        - Brutto Grundlohn: {results['brutto_grundlohn']:.2f} €
        - Rentenversicherung (3,6%): -{results['rentenversicherung']:.2f} €
        - Netto Grundlohn: {(results['brutto_grundlohn'] - results['rentenversicherung']):.2f} €
        - Steuerfreie Zuschläge: +{results['zuschlage']:.2f} €
        - Netto Gesamt: {results['netto']:.2f} €
        - Bis zur Grenze: {results['freibetrag_rest']:.2f} €
        
        Die Zuschläge sind steuerfrei und zählen nicht zur Minijob-Grenze!
        """)
    
    # Monatsübersicht mit verbessertem Balkendiagramm
    st.subheader("Monatsübersicht")
    
    # Daten für alle Monate sammeln
    monthly_comparison = []
    for monat in MONATE:
        data = st.session_state.monthly_data[monat]
        if data['stunden'] > 0:  # Nur Monate mit Arbeitsstunden
            result = calculate_salary(
                data['grundlohn'], data['stunden'],
                data['sf_zuschlag'], data['sf_zuschlag_stunden'],
                data['nacht_zuschlag'], data['nacht_zuschlag_stunden']
            )
            monthly_comparison.append({
                'Monat': monat,
                'Grundlohn': result['brutto_grundlohn'],
                'Zuschläge': result['zuschlage'],
                'Netto': result['netto']
            })
    
    if monthly_comparison:
        df_vergleich = pd.DataFrame(monthly_comparison)
        df_vergleich = df_vergleich.set_index('Monat')
        
        # Farbkodiertes Balkendiagramm
        st.bar_chart(df_vergleich, height=400)
        
        # Detailansicht des aktuellen Monats
        st.write("**Aktueller Monat:**")
        current_data = pd.DataFrame({
            'Kategorie': ['Grundlohn', 'Zuschläge', 'Netto'],
            'Betrag': [
                results['brutto_grundlohn'],
                results['zuschlage'],
                results['netto']
            ]
        })
        st.bar_chart(current_data.set_index('Kategorie'), height=200)
    
    st.sidebar.header("Daten speichern/laden")
    if st.sidebar.button("Daten als CSV exportieren"):
        data_for_export = []
        for month, data in st.session_state.monthly_data.items():
            row = {
                'Monat': month,
                'Grundlohn': data['grundlohn'],
                'Stunden': data['stunden'],
                'SF_Zuschlag': data['sf_zuschlag'],
                'SF_Zuschlag_Stunden': data['sf_zuschlag_stunden'],
                'Nacht_Zuschlag': data['nacht_zuschlag'],
                'Nacht_Zuschlag_Stunden': data['nacht_zuschlag_stunden']
            }
            data_for_export.append(row)
        
        df = pd.DataFrame(data_for_export)
        csv = df.to_csv(index=False)
        st.sidebar.download_button(
            "CSV herunterladen",
            csv,
            "lohnberechnung.csv",
            "text/csv",
            key='download-csv'
        )
    
    uploaded_file = st.sidebar.file_uploader("CSV-Datei laden", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        for _, row in df.iterrows():
            month = row['Monat']
            st.session_state.monthly_data[month] = {
                'grundlohn': row['Grundlohn'],
                'stunden': row['Stunden'],
                'sf_zuschlag': True if str(row['SF_Zuschlag']).lower() == 'true' else False,
                'sf_zuschlag_stunden': row['SF_Zuschlag_Stunden'],
                'nacht_zuschlag': True if str(row['Nacht_Zuschlag']).lower() == 'true' else False,
                'nacht_zuschlag_stunden': row['Nacht_Zuschlag_Stunden']
            }
        st.sidebar.success("Daten erfolgreich geladen!")
    
    st.divider()
    st.info(f"""
    **Hinweise:**
    - Rentenversicherungspflicht: 3,6% des Bruttolohns (ohne Zuschläge)
    - Mindestlohn 2025: {MINDESTLOHN:.2f} €/Stunde
    - SF-Zuschlag (Sonntag-/Feiertagszuschlag) = 30% Aufschlag (steuerfrei)
    - Minijob-Grenze: {MINIJOB_GRENZE:.2f} €/Monat
    - Maximale Arbeitszeit: 42 Stunden/Monat = 10,5 Stunden/Woche
    - Zuschläge sind steuerfrei und zählen nicht zur Minijob-Grenze
    - Vereinfachte Berechnung der Abzüge (30% bei Überschreitung der Minijob-Grenze)
    """)

if __name__ == "__main__":
    main()
