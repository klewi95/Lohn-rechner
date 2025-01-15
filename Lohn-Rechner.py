import streamlit as st
import pandas as pd
from datetime import datetime

# Konstanten
MINDESTLOHN = 12.82
MINIJOB_GRENZE = 556.0

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
    
    # Abzüge berechnen (nur auf Grundlohn, nicht auf Zuschläge)
    abzuge = 0.0
    if brutto_grundlohn > MINIJOB_GRENZE:
        abzuge = brutto_grundlohn * 0.30  # Vereinfachte Abzüge 30%
            
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
        'freibetrag_rest': freibetrag_rest,
        'rest_stunden': rest_stunden
    }

def main():
    st.title("Gehaltsrechner 2025")
    
    # Grundeinstellungen
    col1, col2 = st.columns(2)
    with col1:
        grundlohn = st.number_input(
            "Stundenlohn (€)",
            min_value=MINDESTLOHN,
            value=MINDESTLOHN,
            step=0.5,
            format="%.2f"
        )
    with col2:
        stunden = st.number_input(
            "Stunden pro Monat",
            min_value=0.0,
            value=26.0,
            step=1.0,
            format="%.1f"
        )
    
    # Zuschläge
    st.subheader("Zuschläge (steuerfrei)")
    
    # SE-Zuschlag
    col1, col2 = st.columns(2)
    with col1:
        se_zuschlag = st.checkbox("SE-Zuschlag (30%)")
    with col2:
        se_zuschlag_stunden = st.number_input(
            "Stunden mit SE-Zuschlag",
            min_value=0.0,
            max_value=stunden,
            value=0.0,
            step=1.0,
            format="%.1f",
            disabled=not se_zuschlag
        )
    
    # Nacht-Zuschlag
    col1, col2 = st.columns(2)
    with col1:
        nacht_zuschlag = st.checkbox("Nacht-Zuschlag (25%)")
    with col2:
        nacht_zuschlag_stunden = st.number_input(
            "Stunden mit Nacht-Zuschlag",
            min_value=0.0,
            max_value=stunden,
            value=0.0,
            step=1.0,
            format="%.1f",
            disabled=not nacht_zuschlag
        )
    
    # Berechnung
    results = calculate_salary(
        grundlohn, stunden, 
        se_zuschlag, se_zuschlag_stunden,
        nacht_zuschlag, nacht_zuschlag_stunden
    )
    
    # Ergebnisse anzeigen
    st.divider()
    st.subheader("Ergebnis")
    
    # Grundlohn und Zuschläge
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Brutto Grundlohn", f"{results['brutto_grundlohn']:.2f} €")
    with col2:
        st.metric("Steuerfreie Zuschläge", f"{results['zuschlage']:.2f} €")
    with col3:
        st.metric("Brutto gesamt", f"{results['brutto_gesamt']:.2f} €")
    
    # Netto und Freibetrag
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Netto", f"{results['netto']:.2f} €")
    with col2:
        st.metric("Noch bis Minijob-Grenze", f"{results['freibetrag_rest']:.2f} € ({results['rest_stunden']} Stunden)")
    
    # Warnungen und Hinweise
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
        - Aktueller Grundlohn: {results['brutto_grundlohn']:.2f} €
        - Bis zur Grenze: {results['freibetrag_rest']:.2f} €
        
        Die Zuschläge ({results['zuschlage']:.2f} €) sind steuerfrei und zählen nicht zur Minijob-Grenze!
        """)
    
    # Hinweise
    st.divider()
    st.info(f"""
    **Hinweise:**
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
