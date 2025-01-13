import streamlit as st
import pandas as pd
from datetime import datetime

# Konstanten
MINDESTLOHN = 12.82
MINIJOB_GRENZE = 556.0

def calculate_salary(grundlohn: float, stunden: float, se_zuschlag: bool, 
                    nacht_zuschlag: bool) -> dict:
    """Berechnet das Gehalt mit allen Zuschlägen und Abzügen."""
    
    # Grundlohn berechnen
    brutto_grundlohn = grundlohn * stunden
    
    # Zuschläge berechnen
    zuschlage = 0.0
    if se_zuschlag:
        zuschlage += brutto_grundlohn * 0.3  # 30% Zuschlag
    if nacht_zuschlag:
        zuschlage += brutto_grundlohn * 0.25  # 25% Zuschlag
        
    brutto_gesamt = brutto_grundlohn + zuschlage
    
    # Abzüge berechnen
    abzuge = 0.0
    if brutto_gesamt > MINIJOB_GRENZE:
        abzuge = brutto_gesamt * 0.30  # Vereinfachte Abzüge 30%
            
    netto = brutto_gesamt - abzuge
    
    return {
        'brutto_grundlohn': brutto_grundlohn,
        'zuschlage': zuschlage,
        'brutto_gesamt': brutto_gesamt,
        'netto': netto,
        'abzuge': abzuge
    }

def main():
    st.title("Gehaltsrechner 2025")
    
    # Grundeinstellungen
    grundlohn = st.number_input(
        "Stundenlohn (€)",
        min_value=MINDESTLOHN,
        value=MINDESTLOHN,
        step=0.5,
        format="%.2f"
    )
    
    stunden = st.number_input(
        "Stunden pro Monat",
        min_value=0.0,
        value=26.0,
        step=1.0,
        format="%.1f"
    )
    
    # Zuschläge
    col1, col2 = st.columns(2)
    with col1:
        se_zuschlag = st.checkbox("SE-Zuschlag (30%)")
    with col2:
        nacht_zuschlag = st.checkbox("Nacht-Zuschlag (25%)")
    
    # Berechnung
    results = calculate_salary(grundlohn, stunden, se_zuschlag, nacht_zuschlag)
    
    # Ergebnisse anzeigen
    st.divider()
    st.subheader("Ergebnis")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Brutto Grundlohn", f"{results['brutto_grundlohn']:.2f} €")
        st.metric("Zuschläge", f"{results['zuschlage']:.2f} €")
    with col2:
        st.metric("Brutto gesamt", f"{results['brutto_gesamt']:.2f} €")
        st.metric("Netto", f"{results['netto']:.2f} €")
    
    if results['brutto_gesamt'] > MINIJOB_GRENZE:
        st.warning(f"Achtung: Minijob-Grenze ({MINIJOB_GRENZE:.2f} €) überschritten!")
    
    # Hinweise
    st.divider()
    st.info(f"""
    **Hinweise:**
    - Mindestlohn 2025: {MINDESTLOHN:.2f} €/Stunde
    - Minijob-Grenze: {MINIJOB_GRENZE:.2f} €/Monat
    - Vereinfachte Berechnung der Abzüge (30% bei Überschreitung der Minijob-Grenze)
    """)

if __name__ == "__main__":
    main()
