import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date

# --- KONSTANTEN ---
MINDESTLOHN = 12.82
MINIJOB_GRENZE = 556.0

# Steuersätze und Zuschlagsraten
RATES = {
    "rentenversicherung_minijob": 0.036,
    "sf_zuschlag_rate": 0.30,  # 30% SF-Zuschlag
    "nacht_zuschlag_rate": 0.25, # 25% Nacht-Zuschlag
    "pauschale_abzuege_ueber_minijob": 0.30 # 30% pauschale Abzüge bei Überschreitung
}

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

# --- HILFSFUNKTIONEN ---

def get_status_color(prozent: float) -> str:
    """Gibt die Farbe basierend auf dem Prozentsatz zurück."""
    if prozent > 100:
        return "🔴"
    elif prozent > 85:
        return "🟡"
    else:
        return "🟢"

def get_thermometer_html(prozent: float) -> str:
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

def get_month_calendar_html(year: int, month: int, feiertage: dict) -> str:
    """Erstellt einen HTML-Kalender mit markierten Feiertagen."""
    cal = calendar.monthcalendar(year, month)
    month_name = MONATE[month-1]
    
    # Kalenderstile (einmalig im Header der App laden oder hier belassen)
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
    """Berechnet das Gehalt mit allen Zuschlägen und Abzügen."""
    
    brutto_grundlohn = grundlohn * stunden
    
    zuschlage = 0.0
    if sf_zuschlag:
        sf_stunden = min(sf_zuschlag_stunden, stunden)
        zuschlage += grundlohn * sf_stunden * RATES["sf_zuschlag_rate"]
        
    if nacht_zuschlag:
        nacht_stunden = min(nacht_zuschlag_stunden, stunden)
        zuschlage += grundlohn * nacht_stunden * RATES["nacht_zuschlag_rate"]
            
    brutto_gesamt = brutto_grundlohn + zuschlage
    
    rentenversicherung_abzug = 0.0
    pauschale_abzuege = 0.0
    gesamte_abzuege = 0.0
    
    if brutto_grundlohn <= MINIJOB_GRENZE:
        rentenversicherung_abzug = brutto_grundlohn * RATES["rentenversicherung_minijob"]
        gesamte_abzuege = rentenversicherung_abzug
    else:
        pauschale_abzuege = brutto_grundlohn * RATES["pauschale_abzuege_ueber_minijob"]
        gesamte_abzuege = pauschale_abzuege
            
    netto = brutto_gesamt - gesamte_abzuege
    
    freibetrag_rest = max(0, MINIJOB_GRENZE - brutto_grundlohn)
    rest_stunden = int(freibetrag_rest / grundlohn) if grundlohn > 0 else 0
    
    return {
        'brutto_grundlohn': brutto_grundlohn,
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
    
    # Initialisiere Session State für monatliche Daten
    if 'monthly_data' not in st.session_state:
        st.session_state.monthly_data = {
            month: {
                'grundlohn': MINDESTLOHN,
                'stunden': 24.0,
                'sf_zuschlag': True,
                'sf_zuschlag_stunden': 12.0, # Beispielwert für SF-Stunden
                'nacht_zuschlag': False,
                'nacht_zuschlag_stunden': 0.0
            } for month in MONATE
        }
    
    # Monat auswählen
    selected_month = st.selectbox("Wähle einen Monat aus:", MONATE)
    month_data = st.session_state.monthly_data[selected_month]
    
    st.divider() # Visuelle Trennung
    
    # Kalender mit Feiertagen anzeigen
    current_year = datetime.now().year # Dynamisches Jahr für den Kalender
    month_index = MONATE.index(selected_month) + 1
    calendar_html = get_month_calendar_html(current_year, month_index, FEIERTAGE_NRW_2025)
    st.markdown(calendar_html, unsafe_allow_html=True)
    
    # Feiertage des Monats anzeigen
    feiertage_im_monat = [(day, name) for (m, day), name in FEIERTAGE_NRW_2025.items() if m == month_index]
    if feiertage_im_monat:
        feiertage_text = "\n".join([f"- **{day:02d}.{month_index:02d}.**: {name}" for day, name in feiertage_im_monat])
        st.info(f"""
        **Feiertage in {selected_month} {current_year} (NRW):**
        {feiertage_text}
        
        *An gesetzlichen Feiertagen gilt der SF-Zuschlag (30%).*
        """)
    
    st.divider() # Visuelle Trennung

    # Vorlagen für typische Szenarien
    template = st.selectbox(
        "Lade eine Vorlage für die Stundenanzahl:",
        ["Individuell", "6h/Woche (24h/Monat)", "8h/Woche (32h/Monat)", "10h/Woche (40h/Monat)"]
    )
    
    if template != "Individuell":
        # Wenn eine Vorlage gewählt wird, werden die Stunden aktualisiert
        if template == "6h/Woche (24h/Monat)":
            month_data['stunden'] = 24.0
        elif template == "8h/Woche (32h/Monat)":
            month_data['stunden'] = 32.0
        elif template == "10h/Woche (40h/Monat)":
            month_data['stunden'] = 40.0
        # Optional: Setze Zuschlagsstunden auch zurück oder auf sinnvolle Werte
        month_data['sf_zuschlag_stunden'] = 0.0
        month_data['nacht_zuschlag_stunden'] = 0.0
        
    col1, col2 = st.columns(2)
    with col1:
        grundlohn = st.number_input(
            "Stundenlohn (€):",
            min_value=MINDESTLOHN,
            value=month_data['grundlohn'],
            step=0.5,
            format="%.2f",
            key=f"grundlohn_{selected_month}" # Eindeutiger Key für jeden Monat
        )
    with col2:
        stunden = st.number_input(
            "Arbeitsstunden pro Monat:",
            min_value=0.0,
            value=month_data['stunden'],
            step=1.0,
            format="%.1f",
            key=f"stunden_{selected_month}"
        )
    
    st.subheader("Extra-Zuschläge (steuerfrei)")
    st.info("Diese Zuschläge beeinflussen nicht die Minijob-Grenze.")

    col1, col2 = st.columns(2)
    with col1:
        sf_zuschlag = st.checkbox("Sonntag-/Feiertagszuschlag (30%)", value=month_data['sf_zuschlag'], key=f"sf_check_{selected_month}")
    with col2:
        # Standardwert für sf_zuschlag_stunden sollte 0 sein, wenn nicht aktiv
        sf_zuschlag_stunden_val = month_data['sf_zuschlag_stunden'] if sf_zuschlag else 0.0
        sf_zuschlag_stunden = st.number_input(
            "Stunden mit SF-Zuschlag:",
            min_value=0.0,
            max_value=stunden,
            value=min(sf_zuschlag_stunden_val, stunden), # Sicherstellen, dass der Wert nicht über Stunden liegt
            step=1.0,
            format="%.1f",
            disabled=not sf_zuschlag,
            key=f"sf_stunden_{selected_month}"
        )
    
    col1, col2 = st.columns(2)
    with col1:
        nacht_zuschlag = st.checkbox("Nacht-Zuschlag (25%)", value=month_data['nacht_zuschlag'], key=f"nacht_check_{selected_month}")
    with col2:
        # Standardwert für nacht_zuschlag_stunden sollte 0 sein, wenn nicht aktiv
        nacht_zuschlag_stunden_val = month_data['nacht_zuschlag_stunden'] if nacht_zuschlag else 0.0
        nacht_zuschlag_stunden = st.number_input(
            "Stunden mit Nacht-Zuschlag:",
            min_value=0.0,
            max_value=stunden,
            value=min(nacht_zuschlag_stunden_val, stunden), # Sicherstellen, dass der Wert nicht über Stunden liegt
            step=1.0,
            format="%.1f",
            disabled=not nacht_zuschlag,
            key=f"nacht_stunden_{selected_month}"
        )
        
    # Speichere die aktualisierten Daten im Session State
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
    
    st.divider() # Visuelle Trennung

    # Berechnung des Prozentsatzes und Status
    prozent_ausgeschoepft = (results['brutto_grundlohn'] / MINIJOB_GRENZE) * 100
    status_emoji = get_status_color(prozent_ausgeschoepft)
    
    # Thermometer-Anzeige
    st.subheader(f"📊 Minijob-Grenze Status {status_emoji}")
    st.write(f"**{prozent_ausgeschoepft:.1f}%** der Minijob-Grenze ausgeschöpft (von {MINIJOB_GRENZE:.2f} €)")
    st.markdown(get_thermometer_html(prozent_ausgeschoepft), unsafe_allow_html=True)
    
    # Ergebnisse
    st.subheader("💰 Monatsbeträge im Überblick")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Brutto Grundlohn", f"{results['brutto_grundlohn']:.2f} €")
    with col2:
        st.metric("Steuerfreie Zuschläge", f"{results['zuschlage']:.2f} €")
    with col3:
        st.metric("Brutto Gesamt", f"{results['brutto_gesamt']:.2f} €")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Netto Auszahlung", f"{results['netto']:.2f} €")
    with col2:
        if results['brutto_grundlohn'] <= MINIJOB_GRENZE:
             st.metric("Noch bis Minijob-Grenze", f"{results['freibetrag_rest']:.2f} € ({results['rest_stunden']} Stunden bei {grundlohn:.2f} €/h)")
        else:
             st.metric("Minijob-Grenze überschritten", f"{(results['brutto_grundlohn'] - MINIJOB_GRENZE):.2f} €")

    st.divider() # Visuelle Trennung
    
    if results['brutto_grundlohn'] > MINIJOB_GRENZE:
        st.error(f"""
        **🚨 Achtung: Minijob-Grenze von {MINIJOB_GRENZE:.2f} € überschritten!**
        - Ihr Grundlohn für diesen Monat beträgt: **{results['brutto_grundlohn']:.2f} €**
        - Die Überschreitung beträgt: **{(results['brutto_grundlohn'] - MINIJOB_GRENZE):.2f} €**
        
        *Hinweis: Die hier berechneten Abzüge (pauschal 30%) sind eine Vereinfachung. In der Realität würden bei Überschreitung der Minijob-Grenze volle Sozialversicherungsbeiträge anfallen (Renten-, Kranken-, Pflege- und Arbeitslosenversicherung), was zu deutlich höheren Abzügen führen würde. Die steuerfreien Zuschläge ({results['zuschlage']:.2f} €) zählen nicht zur Minijob-Grenze.*
        """)
    else:
        st.success(f"""
        **🎉 Sie liegen innerhalb der Minijob-Grenze von {MINIJOB_GRENZE:.2f} €!**
        - Brutto Grundlohn: **{results['brutto_grundlohn']:.2f} €**
        - Abzug Rentenversicherung (3,6%): **-{results['rentenversicherung_abzug']:.2f} €**
        - Netto Grundlohn (nach RV-Abzug): **{(results['brutto_grundlohn'] - results['rentenversicherung_abzug']):.2f} €**
        - Steuerfreie Zuschläge: **+{results['zuschlage']:.2f} €**
        - **Netto Auszahlung Gesamt: {results['netto']:.2f} €**
        - Verbleibender Betrag bis zur Grenze: **{results['freibetrag_rest']:.2f} €** (entspricht ca. {results['rest_stunden']} Stunden bei Ihrem Stundenlohn)
        
        *Die Zuschläge sind steuerfrei und zählen nicht zur Minijob-Grenze.*
        """)
    
    st.divider() # Visuelle Trennung

    # Monatsübersicht mit verbessertem Balkendiagramm
    st.subheader("📈 Monatsübersicht & Vergleich")
    
    # Daten für alle Monate sammeln
    monthly_comparison = []
    for monat in MONATE:
        data = st.session_state.monthly_data[monat]
        # Füge nur Monate hinzu, die tatsächlich Stunden oder Zuschläge haben
        if data['stunden'] > 0 or data['sf_zuschlag_stunden'] > 0 or data['nacht_zuschlag_stunden'] > 0:
            result = calculate_salary(
                data['grundlohn'], data['stunden'],
                data['sf_zuschlag'], data['sf_zuschlag_stunden'],
                data['nacht_zuschlag'], data['nacht_zuschlag_stunden']
            )
            monthly_comparison.append({
                'Monat': monat,
                'Brutto Grundlohn': result['brutto_grundlohn'],
                'Zuschläge': result['zuschlage'],
                'Netto': result['netto']
            })
    
    if monthly_comparison:
        df_vergleich = pd.DataFrame(monthly_comparison)
        df_vergleich = df_vergleich.set_index('Monat')
        
        st.write("Vergleich der Monatsbeträge:")
        st.bar_chart(df_vergleich, height=400)
        
        st.write("Detailansicht für den aktuellen Monat:")
        current_data_df = pd.DataFrame({
            'Kategorie': ['Brutto Grundlohn', 'Zuschläge', 'Netto'],
            'Betrag': [
                results['brutto_grundlohn'],
                results['zuschlage'],
                results['netto']
            ]
        }).set_index('Kategorie')
        st.bar_chart(current_data_df, height=200)
    else:
        st.info("Keine Daten für die Monatsübersicht verfügbar. Bitte geben Sie Stunden für mindestens einen Monat ein.")
    
    st.divider() # Visuelle Trennung

    st.sidebar.header("💾 Daten speichern/laden")
    st.sidebar.markdown("Exportieren Sie Ihre Berechnungen oder laden Sie gespeicherte Daten.")

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
        csv = df.to_csv(index=False).encode('utf-8') # UTF-8 Kodierung für Sonderzeichen
        st.sidebar.download_button(
            "CSV herunterladen",
            csv,
            "gehaltsberechnung.csv", # Dateiname angepasst
            "text/csv",
            key='download-csv'
        )
    
    uploaded_file = st.sidebar.file_uploader("CSV-Datei laden", type="csv")
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            # Überprüfen, ob alle notwendigen Spalten vorhanden sind
            required_columns = ['Monat', 'Grundlohn', 'Stunden', 'SF_Zuschlag', 'SF_Zuschlag_Stunden', 'Nacht_Zuschlag', 'Nacht_Zuschlag_Stunden']
            if not all(col in df.columns for col in required_columns):
                st.sidebar.error("Fehler: Die geladene CSV-Datei hat nicht die erwarteten Spalten.")
                return
            
            for _, row in df.iterrows():
                month = row['Monat']
                if month in MONATE: # Sicherstellen, dass der Monat gültig ist
                    st.session_state.monthly_data[month] = {
                        'grundlohn': float(row['Grundlohn']),
                        'stunden': float(row['Stunden']),
                        'sf_zuschlag': str(row['SF_Zuschlag']).lower() == 'true',
                        'sf_zuschlag_stunden': float(row['SF_Zuschlag_Stunden']),
                        'nacht_zuschlag': str(row['Nacht_Zuschlag']).lower() == 'true',
                        'nacht_zuschlag_stunden': float(row['Nacht_Zuschlag_Stunden'])
                    }
                else:
                    st.sidebar.warning(f"Überspringe unbekannten Monat in CSV: {month}")
            st.sidebar.success("Daten erfolgreich geladen!")
            # Workaround, um die Anzeige nach dem Laden zu aktualisieren
            st.experimental_rerun() 
        except Exception as e:
            st.sidebar.error(f"Fehler beim Laden der CSV-Datei: {e}")
            st.sidebar.info("Bitte stellen Sie sicher, dass die CSV-Datei das korrekte Format hat.")

    st.divider()
    st.info(f"""
    **Wichtige Hinweise zur Berechnung:**
    - **Mindestlohn 2025:** Aktuell {MINDESTLOHN:.2f} € pro Stunde.
    - **Minijob-Grenze:** Der Brutto-Grundlohn darf {MINIJOB_GRENZE:.2f} € pro Monat nicht überschreiten.
    - **Rentenversicherungspflicht (Minijob):** 3,6% des Bruttolohns (ohne Zuschläge).
    - **SF-Zuschlag (Sonntag-/Feiertagszuschlag):** 30% Aufschlag auf den Stundenlohn (steuerfrei).
    - **Nacht-Zuschlag:** 25% Aufschlag auf den Stundenlohn (steuerfrei).
    - **Steuerfreie Zuschläge:** Diese zählen *nicht* zur Minijob-Grenze.
    - **Vereinfachte Abzüge:** Bei Überschreitung der Minijob-Grenze wird hier eine **pauschale Abzug von 30%** des Grundlohns angenommen. Dies ist eine Vereinfachung! In der Realität können die Abzüge für Sozialversicherungen (Kranken-, Pflege-, Renten- und Arbeitslosenversicherung) deutlich höher sein.
    - **Maximale Arbeitszeit (orientierend):** ca. 42 Stunden pro Monat (entspricht ca. 10,5 Stunden pro Woche bei einem Monatsdurchschnitt von 4 Wochen).
    """)

if __name__ == "__main__":
    main()
