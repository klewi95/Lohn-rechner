import streamlit as st
import pandas as pd
import datetime

# Konstanten
MINDESTLOHN = 12.82  # Aktueller Mindestlohn 2025
MINIJOB_GRENZE = 556.0  # Minijob-Grenze 2025
MONATE = [
    'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
    'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'
]

def calculate_salary(grundlohn: float, stunden: float, se_zuschlag: bool, se_stunden: float, 
                    se_prozent: float, nacht_zuschlag: bool, nacht_stunden: float, 
                    krankenversicherung: str) -> dict:
    """Berechnet das Gehalt mit allen Zuschlägen und Abzügen."""
    
    # Grundlohn berechnen
    brutto_grundlohn = grundlohn * stunden
    
    # Zuschläge berechnen
    zuschlage = 0.0
    if se_zuschlag:
        zuschlage += grundlohn * min(se_stunden, stunden) * (se_prozent / 100.0)
    if nacht_zuschlag:
        zuschlage += grundlohn * min(nacht_stunden, stunden) * 0.25
        
    brutto_gesamt = brutto_grundlohn + zuschlage
    
    # Abzüge berechnen
    abzuge = {
        'lohnsteuer': 0.0,
        'krankenversicherung': 0.0,
        'rentenversicherung': 0.0,
        'arbeitslosenversicherung': 0.0
    }
    
    if brutto_gesamt > MINIJOB_GRENZE:
        abzuge['lohnsteuer'] = brutto_gesamt * 0.15
        if krankenversicherung == 'Gesetzlich':
            abzuge['krankenversicherung'] = brutto_gesamt * 0.073
            abzuge['rentenversicherung'] = brutto_gesamt * 0.093
            abzuge['arbeitslosenversicherung'] = brutto_gesamt * 0.012
            
    gesamt_abzuge = sum(abzuge.values())
    netto = brutto_gesamt - gesamt_abzuge
    
    return {
        'brutto_grundlohn': brutto_grundlohn,
        'zuschlage': zuschlage,
        'brutto_gesamt': brutto_gesamt,
        'netto': netto,
        'abzuge': abzuge
    }

def main():
    st.set_page_config(page_title="Gehaltsrechner 2025", layout="wide")
    
    st.title("Gehaltsrechner mit Zuschlägen 2025")
    
    # Initialisiere Session State für monatliche Daten
    if 'monthly_data' not in st.session_state:
        st.session_state.monthly_data = {
            month: {
                'calculated': False,
                'results': None,
                'inputs': {
                    'grundlohn': float(MINDESTLOHN),
                    'stunden': 26.0,
                    'se_zuschlag': False,
                    'se_stunden': 0.0,
                    'se_prozent': 30.0,
                    'nacht_zuschlag': False,
                    'nacht_stunden': 0.0,
                    'krankenversicherung': 'Gesetzlich'
                }
            } for month in MONATE
        }
    
    # Erstelle zwei Spalten: Links für Eingabe, rechts für Ergebnisse
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Eingaben")
        
        # Monatsauswahl
        selected_month = st.selectbox(
            "Monat auswählen",
            MONATE,
            index=datetime.datetime.now().month - 1
        )
        
        month_data = st.session_state.monthly_data[selected_month]['inputs']
        
        # Grundlegende Eingaben
        grundlohn = st.number_input(
            "Grundlohn pro Stunde (€)",
            min_value=float(MINDESTLOHN),
            value=float(month_data['grundlohn']),
            step=0.01,
            format="%.2f"
        )
        
        stunden = st.number_input(
            "Stunden pro Monat",
            min_value=0.0,
            value=float(month_data['stunden']),
            step=0.5,
            format="%.1f"
        )
        
        # Zuschläge
        st.subheader("Zuschläge")
        
        se_zuschlag = st.checkbox(
            "SE-Zuschlag",
            value=month_data['se_zuschlag']
        )
        
        if se_zuschlag:
            se_prozent = st.number_input(
                "SE-Zuschlag Prozent",
                min_value=0.0,
                max_value=100.0,
                value=float(month_data['se_prozent']),
                step=1.0,
                format="%.1f"
            )
            se_stunden = st.number_input(
                "Stunden mit SE-Zuschlag",
                min_value=0.0,
                max_value=float(stunden),
                value=min(float(month_data['se_stunden']), float(stunden)),
                step=0.5,
                format="%.1f"
            )
        else:
            se_prozent = 0.0
            se_stunden = 0.0
            
        nacht_zuschlag = st.checkbox(
            "Nacht-Zuschlag (25%)",
            value=month_data['nacht_zuschlag']
        )
        
        if nacht_zuschlag:
            nacht_stunden = st.number_input(
                "Stunden mit Nacht-Zuschlag",
                min_value=0.0,
                max_value=float(stunden),
                value=min(float(month_data['nacht_stunden']), float(stunden)),
                step=0.5,
                format="%.1f"
            )
        else:
            nacht_stunden = 0.0
            
        krankenversicherung = st.selectbox(
            "Krankenversicherung",
            ['Gesetzlich', 'Privat'],
            index=0 if month_data['krankenversicherung'] == 'Gesetzlich' else 1
        )
        
        # Berechnen Button
        if st.button(f"{selected_month} berechnen"):
            # Aktuelle Eingaben speichern
            st.session_state.monthly_data[selected_month]['inputs'] = {
                'grundlohn': float(grundlohn),
                'stunden': float(stunden),
                'se_zuschlag': se_zuschlag,
                'se_stunden': float(se_stunden),
                'se_prozent': float(se_prozent),
                'nacht_zuschlag': nacht_zuschlag,
                'nacht_stunden': float(nacht_stunden),
                'krankenversicherung': krankenversicherung
            }
            
            # Berechnung durchführen
            results = calculate_salary(
                grundlohn, stunden, se_zuschlag, se_stunden, se_prozent,
                nacht_zuschlag, nacht_stunden, krankenversicherung
            )
            
            st.session_state.monthly_data[selected_month]['calculated'] = True
            st.session_state.monthly_data[selected_month]['results'] = results
            
    with col2:
        st.subheader("Ergebnisse")
        
        # Aktuelle Monatsberechnung anzeigen
        if st.session_state.monthly_data[selected_month]['calculated']:
            results = st.session_state.monthly_data[selected_month]['results']
            
            st.write(f"### {selected_month} 2025")
            st.write(f"Brutto Grundlohn: {results['brutto_grundlohn']:.2f} €")
            st.write(f"Zuschläge: {results['zuschlage']:.2f} €")
            st.write(f"Brutto gesamt: {results['brutto_gesamt']:.2f} €")
            st.write(f"**Netto: {results['netto']:.2f} €**")
            
            st.write("#### Abzüge:")
            for name, value in results['abzuge'].items():
                st.write(f"{name.capitalize()}: {value:.2f} €")
        
        # Jahresübersicht
        st.subheader("Jahresübersicht 2025")
        
        calculated_months = [
            month for month in MONATE 
            if st.session_state.monthly_data[month]['calculated']
        ]
        
        if calculated_months:
            jahresbrutto = sum(
                st.session_state.monthly_data[month]['results']['brutto_gesamt']
                for month in calculated_months
            )
            jahresnetto = sum(
                st.session_state.monthly_data[month]['results']['netto']
                for month in calculated_months
            )
            
            st.write(f"Berechnete Monate: {len(calculated_months)}")
            st.write(f"Jahresbrutto (bisher): {jahresbrutto:.2f} €")
            st.write(f"Jahresnetto (bisher): {jahresnetto:.2f} €")
            
            # Monatsübersicht als DataFrame
            df_data = []
            for month in MONATE:
                if st.session_state.monthly_data[month]['calculated']:
                    results = st.session_state.monthly_data[month]['results']
                    df_data.append({
                        'Monat': month,
                        'Brutto': f"{results['brutto_gesamt']:.2f} €",
                        'Netto': f"{results['netto']:.2f} €"
                    })
            
            if df_data:
                st.write("#### Monatsübersicht")
                df = pd.DataFrame(df_data)
                st.dataframe(df, hide_index=True)
        
        # Hinweise
        st.info(f"""
        **Hinweise:**
        - Gesetzlicher Mindestlohn 2025: {MINDESTLOHN:.2f} € pro Stunde
        - Minijob-Grenze 2025: {MINIJOB_GRENZE:.2f} € pro Monat
        - Dies ist eine vereinfachte Berechnung. Die tatsächlichen Abzüge können je nach individueller Situation abweichen.
        """)

if __name__ == "__main__":
    main()
