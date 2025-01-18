import streamlit as st
import pandas as pd

# Konstanten definieren
MINDESTLOHN = 12.82
MINIJOB_GRENZE = 556.0
MONATE = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
          'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']

def calculate_salary(grundlohn, stunden, se_zuschlag, se_zuschlag_stunden,
                    nacht_zuschlag, nacht_zuschlag_stunden):
    # Grundlohn
    brutto_grundlohn = grundlohn * stunden
    
    # Zuschläge
    zuschlage = 0.0
    if se_zuschlag:
        se_stunden = min(se_zuschlag_stunden, stunden)
        zuschlage += grundlohn * se_stunden * 0.3
    if nacht_zuschlag:
        nacht_stunden = min(nacht_zuschlag_stunden, stunden)
        zuschlage += grundlohn * nacht_stunden * 0.25
    
    # Gesamtbrutto
    brutto_gesamt = brutto_grundlohn + zuschlage
    
    # Abzüge
    rentenversicherung = brutto_grundlohn * 0.036
    
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
        'rentenversicherung': rentenversicherung if brutto_grundlohn <= MINIJOB_GRENZE else 0.0,
        'freibetrag_rest': freibetrag_rest,
        'rest_stunden': rest_stunden
    }

def main():
    st.set_page_config(page_title="Gehaltsrechner 2025")
    st.title("Gehaltsrechner 2025")
    
    # Session State initialisieren
    if 'monthly_data' not in st.session_state:
        st.session_state.monthly_data = {
            month: {
                'grundlohn': 12.82,
                'stunden': 24.0,
                'se_zuschlag': True,
                'se_zuschlag_stunden': 12.0,
                'nacht_zuschlag': False,
                'nacht_zuschlag_stunden': 0.0
            } for month in MONATE
        }
    
    # Monatsauswahl
    selected_month = st.selectbox("Monat auswählen", MONATE)
    current_data = st.session_state.monthly_data[selected_month]
    
    # Eingabefelder
    grundlohn = st.number_input("Stundenlohn (€)", 
                               min_value=12.82, 
                               value=current_data['grundlohn'],
                               step=0.01)
    
    stunden = st.number_input("Stunden pro Monat",
                             min_value=0.0,
                             value=current_data['stunden'],
                             step=1.0)
    
    st.subheader("Zuschläge (steuerfrei)")
    se_zuschlag = st.checkbox("SE-Zuschlag (30%)", 
                             value=current_data['se_zuschlag'])
    
    if se_zuschlag:
        se_zuschlag_stunden = st.number_input("Stunden mit SE-Zuschlag",
                                             min_value=0.0,
                                             max_value=stunden,
                                             value=current_data['se_zuschlag_stunden'],
                                             step=1.0)
    else:
        se_zuschlag_stunden = 0.0
    
    nacht_zuschlag = st.checkbox("Nacht-Zuschlag (25%)", 
                                value=current_data['nacht_zuschlag'])
    
    if nacht_zuschlag:
        nacht_zuschlag_stunden = st.number_input("Stunden mit Nacht-Zuschlag",
                                                min_value=0.0,
                                                max_value=stunden,
                                                value=current_data['nacht_zuschlag_stunden'],
                                                step=1.0)
    else:
        nacht_zuschlag_stunden = 0.0
    
    # Daten speichern
    st.session_state.monthly_data[selected_month] = {
        'grundlohn': grundlohn,
        'stunden': stunden,
        'se_zuschlag': se_zuschlag,
        'se_zuschlag_stunden': se_zuschlag_stunden,
        'nacht_zuschlag': nacht_zuschlag,
        'nacht_zuschlag_stunden': nacht_zuschlag_stunden
    }
    
    # Berechnung
    results = calculate_salary(grundlohn, stunden, se_zuschlag, se_zuschlag_stunden,
                             nacht_zuschlag, nacht_zuschlag_stunden)
    
    # Ergebnisse anzeigen
    st.divider()
    st.subheader("Ergebnis")
    
    # Grundwerte
    st.write(f"Brutto Grundlohn: {results['brutto_grundlohn']:.2f} €")
    st.write(f"Steuerfreie Zuschläge: {results['zuschlage']:.2f} €")
    st.write(f"Brutto gesamt: {results['brutto_gesamt']:.2f} €")
    
    # Netto und Freibetrag
    st.write(f"Netto: {results['netto']:.2f} €")
    st.write(f"Noch bis Minijob-Grenze: {results['freibetrag_rest']:.2f} € ({results['rest_stunden']} Stunden)")
    
    # Status
    if results['brutto_grundlohn'] > MINIJOB_GRENZE:
        st.error("""
        Minijob-Grenze überschritten!
        Die Zuschläge sind steuerfrei und zählen nicht zur Minijob-Grenze.
        """)
    else:
        st.success("""
        Innerhalb der Minijob-Grenze ✓
        Die Zuschläge sind steuerfrei und zählen nicht zur Minijob-Grenze.
        """)
    
    # Export/Import
    st.sidebar.header("Daten speichern/laden")
    
    if st.sidebar.button("Daten exportieren"):
        df = pd.DataFrame(st.session_state.monthly_data).T
        df.index.name = 'Monat'
        csv = df.to_csv()
        st.sidebar.download_button(
            "CSV herunterladen",
            csv,
            "lohnberechnung.csv",
            "text/csv"
        )
    
    uploaded_file = st.sidebar.file_uploader("CSV-Datei laden", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, index_col='Monat')
        for month in MONATE:
            if month in df.index:
                st.session_state.monthly_data[month] = df.loc[month].to_dict()
        st.sidebar.success("Daten geladen!")
    
    # Hinweise
    st.divider()
    st.info("""
    Hinweise:
    - Rentenversicherungspflicht: 3,6% des Bruttolohns (ohne Zuschläge)
    - Zuschläge sind steuerfrei und zählen nicht zur Minijob-Grenze
    - Vereinfachte Berechnung der Abzüge (30% bei Überschreitung der Minijob-Grenze)
    """)

if __name__ == "__main__":
    main()