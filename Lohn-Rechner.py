import streamlit as st
import pandas as pd
from datetime import datetime

# Konstanten
MINDESTLOHN = 12.82
MINIJOB_GRENZE = 556.0
MONATE = [
    'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
    'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'
]

def calculate_salary(grundlohn: float, stunden: float, 
                    se_zuschlag: bool, se_zuschlag_stunden: float,
                    nacht_zuschlag: bool, nacht_zuschlag_stunden: float) -> dict:
    """Berechnet das Gehalt mit allen Zuschlägen und Abzügen."""
    
    # Grundlohn berechnen (relevant für Minijob-Grenze)
    brutto_grundlohn = grundlohn * stunden
    
    # Zuschläge berechnen (steuerfrei)
    zuschlage = 0.0
    if se_zuschlag:
        se_stunden = min(se_zuschlag_stunden, stunden)  # Nicht mehr Zuschlagsstunden als Gesamtstunden
        zuschlage += grundlohn * se_stunden * 0.3  # 30% Zuschlag
    if nacht_zuschlag:
        nacht_stunden = min(nacht_zuschlag_stunden, stunden)  # Nicht mehr Zuschlagsstunden als Gesamtstunden
        zuschlage += grundlohn * nacht_stunden * 0.25  # 25% Zuschlag
        
    # Gesamtbrutto (mit Zuschlägen)
    brutto_gesamt = brutto_grundlohn + zuschlage
    
    # Abzüge berechnen
    rentenversicherung = brutto_grundlohn * 0.036  # 3,6% Rentenversicherung für Minijobs
    if brutto_grundlohn > MINIJOB_GRENZE:
        # Bei Überschreitung: vereinfachte Abzüge 30% statt Rentenversicherung
        abzuge = brutto_grundlohn * 0.30
    else:
        # Im Minijob: nur Rentenversicherung
        abzuge = rentenversicherung
            
    netto = brutto_gesamt - abzuge
    
    # Berechnung der verbleibenden Freibetragsgrenze
    freibetrag_rest = max(0, MINIJOB_GRENZE - brutto_grundlohn)
    
    # Berechnung der möglichen Reststunden (abgerundet)
    rest_stunden = int(freibetrag_rest / grundlohn)  # int() rundet nach unten ab
    
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
    # Sicherstellen, dass die Konstanten als global erkannt werden
    global MINDESTLOHN, MINIJOB_GRENZE, MONATE
    
    st.set_page_config(page_title="Gehaltsrechner 2025", layout="wide")
    st.title("Gehaltsrechner mit Zuschlägen 2025")
    
    # Initialisiere Session State für monatliche Daten
    if 'monthly_data' not in st.session_state:
        st.session_state.monthly_data = {
            month: {
                'grundlohn': MINDESTLOHN,
                'stunden': 24.0,  # Standardwert: 24 Stunden
                'se_zuschlag': True,
                'se_zuschlag_stunden': 12.0,  # Standardwert: 12 Stunden
                'nacht_zuschlag': False,
                'nacht_zuschlag_stunden': 0.0
            } for month in MONATE
        }
    
    # Rest der Funktion bleibt unverändert ...
    selected_month = st.selectbox("Monat auswählen", MONATE)
    month_data = st.session_state.monthly_data[selected_month]
    
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
        se_zuschlag = st.checkbox("SE-Zuschlag (30%)", value=month_data['se_zuschlag'])
    with col2:
        se_zuschlag_stunden = st.number_input(
            "Stunden mit SE-Zuschlag",
            min_value=0.0,
            max_value=stunden,
            value=month_data['se_zuschlag_stunden'],
            step=1.0,
            format="%.1f",
            disabled=not se_zuschlag
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
        'se_zuschlag': se_zuschlag,
        'se_zuschlag_stunden': se_zuschlag_stunden,
        'nacht_zuschlag': nacht_zuschlag,
        'nacht_zuschlag_stunden': nacht_zuschlag_stunden
    }
    
    results = calculate_salary(
        grundlohn, stunden, 
        se_zuschlag, se_zuschlag_stunden,
        nacht_zuschlag, nacht_zuschlag_stunden
    )
    
    st.divider()
    st.subheader("Ergebnis")
    
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
    
    st.sidebar.header("Daten speichern/laden")
    
    if st.sidebar.button("Daten als CSV exportieren"):
        data_for_export = []
        for month, data in st.session_state.monthly_data.items():
            row = {
                'Monat': month,
                'Grundlohn': data['grundlohn'],
                'Stunden': data['stunden'],
                'SE_Zuschlag': data['se_zuschlag'],
                'SE_Zuschlag_Stunden': data['se_zuschlag_stunden'],
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
                'se_zuschlag': True if str(row['SE_Zuschlag']).lower() == 'true' else False,
                'se_zuschlag_stunden': row['SE_Zuschlag_Stunden'],
                'nacht_zuschlag': True if str(row['Nacht_Zuschlag']).lower() == 'true' else False,
                'nacht_zuschlag_stunden': row['Nacht_Zuschlag_Stunden']
            }
        st.sidebar.success("Daten erfolgreich geladen!")
    
    st.divider()
    st.info(f"""
    **Hinweise:**
    - Rentenversicherungspflicht: 3,6% des Bruttolohns (ohne Zuschläge)
    - Mindestlohn 2025: {MINDESTLOHN:.2f} €/Stunde
    - inklusive SF-Zuschlag: +3,846 € = 16,666 €
    - Minijob-Grenze: {MINIJOB_GRENZE:.2f} €/Monat
    - Maximale Arbeitszeit: 42 Stunden/Monat = 10,5 Stunden/Woche
    - Monatslohn bei 6h/w: 307,68 € + 46,152 € = 353,832 €
    - Monatslohn bei 8h/w: 410,24 + 61,536 = 471,776 € (8h/w); 
    - Monatslohn bei 10h/w: 512,8 + 76,92 = 589,72 € (10h/w)
    - Zuschläge sind steuerfrei und zählen nicht zur Minijob-Grenze
    - Vereinfachte Berechnung der Abzüge (30% bei Überschreitung der Minijob-Grenze)
    """)

if __name__ == "__main__":
    main()