import streamlit as st
import pandas as pd
import requests
import numpy as np
from datetime import datetime
import os

st.set_page_config(page_title="Calcolatore Tragitto", layout="wide")

st.title("Calcolatore del Tragitto Minimo Casa-Lavoro")

# Funzione per caricare il file CSV
def load_csv(uploaded_file):
    if uploaded_file is not None:
        try:
            # Prova prima con punto e virgola come separatore (formato italiano comune)
            df = pd.read_csv(uploaded_file, sep=";")
            # Controlla se abbiamo le colonne attese
            if not all(col in df.columns for col in ["CASA", "LAVORO", "GIORNO"]):
                # Prova con virgola come separatore
                df = pd.read_csv(uploaded_file, sep=",")
            
            # Pulisci gli spazi bianchi nelle intestazioni
            df.columns = df.columns.str.strip()
            return df
        except Exception as e:
            st.error(f"Errore nel caricamento del file: {e}")
            return None
    return None

# Funzione per geocodificare un indirizzo usando OpenStreetMap Nominatim API
def geocode_address(address):
    try:
        base_url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": address,
            "format": "json",
            "limit": 1
        }
        headers = {
            "User-Agent": "TragittoCalculator/1.0"  # Necessario per le regole di Nominatim
        }
        
        response = requests.get(base_url, params=params, headers=headers)
        data = response.json()
        
        if data and len(data) > 0:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon
        else:
            return None
    except Exception as e:
        st.error(f"Errore durante la geocodifica: {e}")
        return None

# Funzione per calcolare il percorso tra due punti usando OSRM
def get_route(start_coords, end_coords):
    try:
        base_url = "http://router.project-osrm.org/route/v1/driving/"
        url = f"{base_url}{start_coords[1]},{start_coords[0]};{end_coords[1]},{end_coords[0]}"
        params = {
            "overview": "full",
            "geometries": "geojson"
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data["code"] == "Ok":
            route = data["routes"][0]
            distance = route["distance"] / 1000  # Converti in km
            duration = route["duration"] / 60  # Converti in minuti
            return distance, duration
        else:
            st.warning("Non è stato possibile calcolare il percorso")
            return None, None
    except Exception as e:
        st.error(f"Errore durante il calcolo del percorso: {e}")
        return None, None

# Sezione per il caricamento del file
uploaded_file = st.file_uploader("Carica il tuo file CSV", type=["csv"])

if uploaded_file:
    df = load_csv(uploaded_file)
    
    if df is not None:
        st.success("File caricato con successo!")
        
        # Mostra anteprima dei dati
        st.subheader("Anteprima dei dati")
        st.dataframe(df.head())
        
        # Processo di aggiunta degli indirizzi se necessario
        if df.empty or (len(df) == 1 and df.iloc[0].isna().all()):
            st.info("Il file CSV è vuoto. Aggiungi i tuoi indirizzi.")
            
            with st.form("add_address_form"):
                casa = st.text_input("Indirizzo di casa")
                lavoro = st.text_input("Indirizzo di lavoro")
                giorno = st.date_input("Giorno", datetime.now())
                
                submit = st.form_submit_button("Aggiungi")
                
                if submit and casa and lavoro:
                    new_row = pd.DataFrame({"CASA": [casa], "LAVORO": [lavoro], "GIORNO": [giorno.strftime("%d/%m/%Y")]})
                    df = pd.concat([df, new_row], ignore_index=True)
                    st.success("Indirizzo aggiunto!")
                    st.dataframe(df)
        
        # Sezione per selezionare un giorno dal CSV
        if not df.empty:
            giorni_disponibili = df["GIORNO"].unique().tolist()
            
            if giorni_disponibili:
                giorno_selezionato = st.selectbox("Seleziona un giorno", giorni_disponibili)
                
                if st.button("Calcola Tragitto"):
                    # Filtra per il giorno selezionato
                    filtered_df = df[df["GIORNO"] == giorno_selezionato]
                    
                    if not filtered_df.empty:
                        indirizzo_casa = filtered_df["CASA"].iloc[0]
                        indirizzo_lavoro = filtered_df["LAVORO"].iloc[0]
                        
                        # Geocodifica gli indirizzi
                        with st.spinner("Geocodifica degli indirizzi in corso..."):
                            coords_casa = geocode_address(indirizzo_casa)
                            coords_lavoro = geocode_address(indirizzo_lavoro)
                        
                        if coords_casa and coords_lavoro:
                            # Calcola il percorso (andata e ritorno)
                            with st.spinner("Calcolo del percorso in corso..."):
                                distance_andata, duration_andata = get_route(coords_casa, coords_lavoro)
                                distance_ritorno, duration_ritorno = get_route(coords_lavoro, coords_casa)
                            
                            if distance_andata and distance_ritorno:
                                # Mostra i risultati
                                st.subheader("Dettagli del Tragitto")
                                st.write(f"**Casa:** {indirizzo_casa}")
                                st.write(f"**Lavoro:** {indirizzo_lavoro}")
                                st.write(f"**Giorno:** {giorno_selezionato}")
                                st.write(f"**Distanza totale:** {distance_andata + distance_ritorno:.2f} km")
                                st.write(f"**Tempo totale stimato:** {(duration_andata + duration_ritorno):.0f} minuti")
                                
                                st.write("---")
                                st.write("**Dettagli Andata:**")
                                st.write(f"Distanza: {distance_andata:.2f} km")
                                st.write(f"Tempo stimato: {duration_andata:.0f} minuti")
                                
                                st.write("**Dettagli Ritorno:**")
                                st.write(f"Distanza: {distance_ritorno:.2f} km")
                                st.write(f"Tempo stimato: {duration_ritorno:.0f} minuti")
                                
                                # Visualizzazione delle coordinate
                                st.subheader("Coordinate")
                                st.write(f"**Casa:** Latitudine {coords_casa[0]}, Longitudine {coords_casa[1]}")
                                st.write(f"**Lavoro:** Latitudine {coords_lavoro[0]}, Longitudine {coords_lavoro[1]}")
                                
                                # Link a Google Maps
                                st.subheader("Visualizza su Google Maps")
                                google_maps_url = f"https://www.google.com/maps/dir/?api=1&origin={coords_casa[0]},{coords_casa[1]}&destination={coords_lavoro[0]},{coords_lavoro[1]}&travelmode=driving"
                                st.markdown(f"[Apri percorso Casa → Lavoro in Google Maps]({google_maps_url})")
                                
                                google_maps_return_url = f"https://www.google.com/maps/dir/?api=1&origin={coords_lavoro[0]},{coords_lavoro[1]}&destination={coords_casa[0]},{coords_casa[1]}&travelmode=driving"
                                st.markdown(f"[Apri percorso Lavoro → Casa in Google Maps]({google_maps_return_url})")
                            else:
                                st.error("Non è stato possibile calcolare il percorso.")
                        else:
                            st.error("Non è stato possibile trovare le coordinate degli indirizzi.")
            else:
                st.warning("Nessun giorno trovato nel file CSV.")
else:
    st.info("Carica un file CSV con colonne 'CASA', 'LAVORO' e 'GIORNO' per iniziare.")
    
    # Aggiungi opzione per creare un nuovo file
    if st.button("Crea nuovo file"):
        # Crea un DataFrame vuoto con le colonne necessarie
        df = pd.DataFrame(columns=["CASA", "LAVORO", "GIORNO"])
        
        # Aggiungi interfaccia per inserire i dati
        with st.form("create_new_form"):
            casa = st.text_input("Indirizzo di casa")
            lavoro = st.text_input("Indirizzo di lavoro")
            giorno = st.date_input("Giorno", datetime.now())
            
            submit = st.form_submit_button("Aggiungi")
            
            if submit and casa and lavoro:
                new_row = pd.DataFrame({
                    "CASA": [casa], 
                    "LAVORO": [lavoro], 
                    "GIORNO": [giorno.strftime("%d/%m/%Y")]
                })
                df = pd.concat([df, new_row], ignore_index=True)
                
                # Scarica il file creato
                csv = df.to_csv(sep=";", index=False)
                st.download_button(
                    label="Scarica CSV",
                    data=csv,
                    file_name="indirizzi.csv",
                    mime="text/csv"
                )
                
                st.success("File creato con successo!")
                st.dataframe(df)

# Aggiungi istruzioni d'uso
with st.expander("Come usare questa applicazione"):
    st.markdown("""
    ### Istruzioni per l'uso
    
    1. **Carica il tuo file CSV** con le colonne CASA, LAVORO e GIORNO.
    2. **Seleziona un giorno** dalla lista dei giorni disponibili.
    3. **Premi 'Calcola Tragitto'** per vedere il percorso minimo tra casa e lavoro.
    
    ### Formato del file CSV
    
    Il file CSV deve avere le seguenti colonne:
    - **CASA**: indirizzo completo dell'abitazione
    - **LAVORO**: indirizzo completo del posto di lavoro
    - **GIORNO**: data nel formato GG/MM/AAAA
    
    Esempio:
    ```
    CASA;LAVORO;GIORNO
    Via Roma 1, Milano;Via Dante 15, Milano;01/05/2025
    ```
    
    ### Note
    - L'applicazione utilizza API gratuite (OpenStreetMap e OSRM) per la geocodifica e il calcolo del percorso.
    - I risultati mostrano sia il tragitto di andata che quello di ritorno, iniziando e finendo sempre dall'indirizzo 'CASA'.
    """)

# Footer con informazioni
st.markdown("---")
st.markdown("Applicazione creata con Streamlit. Utilizza le API gratuite di OpenStreetMap e OSRM.")
