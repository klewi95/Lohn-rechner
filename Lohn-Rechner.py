import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gehaltsrechner 2025")
st.title("Gehaltsrechner 2025")

# Konstanten
mindestlohn = 12.82
minijob_grenze = 556.0
monate = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
          'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']

# Session State initialisieren
if 'monatsdaten' not in st.session_state:
    st.session_state.monatsdaten = {}
    for monat in monate:
        st.session_state.monatsdaten[monat] = {
            'grundlohn': 12.82,
            'stunden': 24.0,
            'se_zuschlag': True,
            'se_stunden': 12.0,
            'nacht_zuschlag': False,
            'nacht_stunden': 0.0
        }

# Monatsauswahl
selected_month = st.selectbox("Monat auswählen", monate)
current_data = st.session_state.monatsdaten[selected_month]

# Grundeinstellungen
grundlohn = st.number_input(
    "Stundenlohn (€)",
    value=float(current_data['grundlohn']),
    min_value=float(mindestlohn),
    step=0.01
)

stunden = st.number_input(
    "Stunden pro Monat",
    value=float(current_data['stunden']),
    min_value=0.0,
    step=1.0
)

# Zuschläge
st.subheader("Zuschläge (steuerfrei)")

se_zuschlag = st.checkbox("SE-Zuschlag (30%)", value=current_data['se_zuschlag'])
if se_zuschlag:
    se_stunden = st.number_input(
        "Stunden mit SE-Zuschlag",
        value=float(current_data['se_stunden']),
        min_value=0.0,
        max_value=float(stunden),
        step=1.0
    )
else:
    se_stunden = 0.0

nacht_zuschlag = st.checkbox("Nacht-Zuschlag (25%)", value=current_data['nacht_zuschlag'])
if nacht_zuschlag:
    nacht_stunden = st.number_input(
        "Stunden mit Nacht-Zuschlag",
        value=float(current_data['nacht_stunden']),
        min_value=0.0,
        max_value=float(stunden),
        step=1.0
    )
else:
    nacht_stunden = 0.0

# Aktuelle Eingaben speichern
st.session_state.monatsdaten[selected_month] = {
    'grundlohn': grundlohn,
    'stunden': stunden,
    'se_zuschlag': se_zuschlag,
    'se_stunden': se_stunden,
    'nacht_zuschlag': nacht_zuschlag,
    'nacht_stunden': nacht_stunden
}

# Berechnung
brutto_grundlohn = grundlohn * stunden

# Zuschläge berechnen
zuschlage = 0.0
if se_zuschlag:
    zuschlage += grundlohn * min(se_stunden, stunden) * 0.3
if nacht_zuschlag:
    zuschlage += grundlohn * min(nacht_stunden, stunden) * 0.25

brutto_gesamt = brutto_grundlohn + zuschlage

# Abzüge berechnen
rentenversicherung = brutto_grundlohn * 0.036

if brutto_grundlohn > minijob_grenze:
    abzuge = brutto_grundlohn * 0.30
else:
    abzuge = rentenversicherung

netto = brutto_gesamt - abzuge
freibetrag_rest = max(0, minijob_grenze - brutto_grundlohn)
rest_stunden = int(freibetrag_rest / grundlohn)

# Ergebnisse anzeigen
st.divider()
st.subheader("Ergebnis")

col1, col2 = st.columns(2)
with col1:
    st.write(f"Brutto Grundlohn: {brutto_grundlohn:.2f} €")
    st.write(f"Steuerfreie Zuschläge: {zuschlage:.2f} €")
    st.write(f"Brutto gesamt: {brutto_gesamt:.2f} €")

with col2:
    st.write(f"Netto: {netto:.2f} €")
    st.write(f"Noch bis Minijob-Grenze: {freibetrag_rest:.2f} € ({rest_stunden} Stunden)")

if brutto_grundlohn > minijob_grenze:
    st.error(f"""
    Minijob-Grenze überschritten!
    - Grundlohn: {brutto_grundlohn:.2f} €
    - Grenze: {minijob_grenze:.2f} €
    - Überschreitung: {(brutto_grundlohn - minijob_grenze):.2f} €
    """)
else:
    st.success(f"""
    Innerhalb der Minijob-Grenze ✓
    - Brutto Grundlohn: {brutto_grundlohn:.2f} €
    - Rentenversicherung (3,6%): -{rentenversicherung:.2f} €
    - Netto Grundlohn: {(brutto_grundlohn - rentenversicherung):.2f} €
    - Steuerfreie Zuschläge: +{zuschlage:.2f} €
    - Netto Gesamt: {netto:.2f} €
    """)

# Export/Import
st.sidebar.header("Daten speichern/laden")

if st.sidebar.button("Daten exportieren"):
    df = pd.DataFrame.from_dict(st.session_state.monatsdaten, orient='index')
    csv = df.to_csv()
    st.sidebar.download_button(
        "CSV herunterladen",
        csv,
        "lohnberechnung.csv",
        "text/csv"
    )

uploaded_file = st.sidebar.file_uploader("CSV-Datei laden", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, index_col=0)
    for monat in monate:
        if monat in df.index:
            st.session_state.monatsdaten[monat] = df.loc[monat].to_dict()
    st.sidebar.success("Daten geladen!")

# Hinweise
st.divider()
st.info("""
**Hinweise:**
- Rentenversicherungspflicht: 3,6% des Bruttolohns (ohne Zuschläge)
- Mindestlohn 2025: 12,82 €/Stunde
- Minijob-Grenze: 556,00 €/Monat
- Zuschläge sind steuerfrei und zählen nicht zur Minijob-Grenze
- Vereinfachte Berechnung der Abzüge (30% bei Überschreitung der Minijob-Grenze)
""")