import streamlit as st
import pandas as pd
import requests
import numpy as np
from datetime import datetime
import itertools
import os

st.set_page_config(page_title="Calcolatore Tragitto Multi-Tappa", layout="wide")

st.title("Calcolatore del Tragitto Minimo tra Casa e Lavori")

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

# Funzione per calcolare la matrice delle distanze tra tutti i punti
def calculate_distance_matrix(coords_list):
    n = len(coords_list)
    distances = np.zeros((n, n))
    durations = np.zeros((n, n))
    
    for i in range(n):
        for j in range(n):
            if i != j:
                dist, dur = get_route(coords_list[i], coords_list[j])
                if dist is not None and dur is not None:
                    distances[i, j] = dist
                    durations[i, j] = dur
                else:
                    st.error(f"Impossibile calcolare la distanza tra i punti {i} e {j}")
                    return None, None
    
    return distances, durations

# Funzione per trovare il percorso ottimale (algoritmo greedy)
def find_optimal_route(distances, start_index):
    n = distances.shape[0]
    current = start_index
    path = [current]
    remaining = set(range(n))
    remaining.remove(current)
    
    # Se abbiamo solo casa e un lavoro
    if n <= 2:
        return list(range(n))
    
    # Percorso con casa -> lavori -> casa
    while remaining:
        if len(remaining) == 1 and 0 in remaining:
            # Se è rimasto solo casa (0), aggiungiamolo
            next_stop = 0
        else:
            # Trova il prossimo posto più vicino (non casa se ci sono ancora altri posti)
            next_stop = min(
                [i for i in remaining if (i != 0 or len(remaining) == 1)],
                key=lambda x: distances[current, x]
            )
        
        path.append(next_stop)
        remaining.remove(next_stop)
        current = next_stop
    
    # Se non torniamo a casa alla fine, aggiungiamo casa
    if path[-1] != 0:
        path.append(0)
    
    return path

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
                
                if st.button("Calcola Tragitto Ottimale"):
                    # Filtra per il giorno selezionato
                    filtered_df = df[df["GIORNO"] == giorno_selezionato]
                    
                    if not filtered_df.empty:
                        # Ottieni tutti gli indirizzi unici per quel giorno
                        casa_address = filtered_df["CASA"].iloc[0]  # Prendiamo il primo indirizzo casa come punto di partenza
                        lavoro_addresses = filtered_df["LAVORO"].unique().tolist()
                        
                        st.write(f"**Giorno selezionato:** {giorno_selezionato}")
                        st.write(f"**Indirizzo casa:** {casa_address}")
                        st.write(f"**Indirizzi lavoro ({len(lavoro_addresses)}):**")
                        for i, addr in enumerate(lavoro_addresses, 1):
                            st.write(f"{i}. {addr}")
                        
                        # Geocodifica tutti gli indirizzi
                        with st.spinner("Geocodifica degli indirizzi in corso..."):
                            coords_casa = geocode_address(casa_address)
                            
                            if coords_casa is None:
                                st.error(f"Impossibile geocodificare l'indirizzo di casa: {casa_address}")
                                st.stop()
                            
                            coords_lavoro_list = []
                            for addr in lavoro_addresses:
                                coords = geocode_address(addr)
                                if coords is None:
                                    st.error(f"Impossibile geocodificare l'indirizzo di lavoro: {addr}")
                                    st.stop()
                                coords_lavoro_list.append(coords)
                        
                        # Crea lista completa di coordinate con casa come prima posizione
                        all_coords = [coords_casa] + coords_lavoro_list
                        all_addresses = [casa_address] + lavoro_addresses
                        
                        # Calcola la matrice delle distanze
                        with st.spinner("Calcolo delle distanze tra tutti i punti..."):
                            distances, durations = calculate_distance_matrix(all_coords)
                            
                            if distances is None or durations is None:
                                st.error("Impossibile calcolare la matrice delle distanze.")
                                st.stop()
                        
                        # Trova il percorso ottimale
                        with st.spinner("Calcolo del percorso ottimale..."):
                            # Casa è sempre indice 0
                            optimal_route = find_optimal_route(distances, 0)
                            
                            # Calcola la distanza totale e la durata
                            total_distance = 0
                            total_duration = 0
                            
                            for i in range(len(optimal_route) - 1):
                                from_idx = optimal_route[i]
                                to_idx = optimal_route[i + 1]
                                total_distance += distances[from_idx, to_idx]
                                total_duration += durations[from_idx, to_idx]
                        
                        # Mostra i risultati
                        st.subheader("Percorso Ottimale")
                        
                        # Tabella del percorso
                        route_data = []
                        for i in range(len(optimal_route)):
                            idx = optimal_route[i]
                            address = all_addresses[idx]
                            address_type = "Casa" if idx == 0 else "Lavoro"
                            
                            # Calcola distanza dal punto precedente (tranne per il primo punto)
                            distance_from_prev = None
                            if i > 0:
                                prev_idx = optimal_route[i-1]
                                distance_from_prev = distances[prev_idx, idx]
                            
                            route_data.append({
                                "Tappa": i + 1,
                                "Tipo": address_type,
                                "Indirizzo": address,
                                "Distanza dalla tappa precedente (km)": f"{distance_from_prev:.2f}" if distance_from_prev is not None else "-"
                            })
                        
                        route_df = pd.DataFrame(route_data)
                        st.table(route_df)
                        
                        # Riepilogo totali
                        st.subheader("Riepilogo")
                        st.write(f"**Distanza totale:** {total_distance:.2f} km")
                        st.write(f"**Tempo totale stimato:** {total_duration:.0f} minuti")
                        
                        # Creazione di link per visualizzare l'intero percorso su Google Maps
                        st.subheader("Visualizza su Google Maps")
                        
                        waypoints = []
                        for i in range(1, len(optimal_route) - 1):  # Escludi il primo e l'ultimo (Casa -> Lavori -> Casa)
                            idx = optimal_route[i]
                            waypoints.append(f"{all_coords[idx][0]},{all_coords[idx][1]}")
                        
                        # Link a Google Maps con waypoints
                        if waypoints:
                            start_coords = all_coords[optimal_route[0]]
                            end_coords = all_coords[optimal_route[-1]]
                            waypoints_str = "|".join(waypoints)
                            
                            google_maps_url = (
                                f"https://www.google.com/maps/dir/?api=1"
                                f"&origin={start_coords[0]},{start_coords[1]}"
                                f"&destination={end_coords[0]},{end_coords[1]}"
                                f"&waypoints={waypoints_str}"
                                f"&travelmode=driving"
                            )
                            
                            st.markdown(f"[Apri intero percorso in Google Maps]({google_maps_url})")
                        else:
                            # Se c'è solo un punto lavoro
                            google_maps_url = (
                                f"https://www.google.com/maps/dir/?api=1"
                                f"&origin={all_coords[optimal_route[0]][0]},{all_coords[optimal_route[0]][1]}"
                                f"&destination={all_coords[optimal_route[-1]][0]},{all_coords[optimal_route[-1]][1]}"
                                f"&travelmode=driving"
                            )
                            
                            st.markdown(f"[Apri percorso in Google Maps]({google_maps_url})")
                        
                        # Link singoli per ogni segmento del percorso
                        with st.expander("Link ai segmenti del percorso"):
                            for i in range(len(optimal_route) - 1):
                                from_idx = optimal_route[i]
                                to_idx = optimal_route[i + 1]
                                
                                from_coords = all_coords[from_idx]
                                to_coords = all_coords[to_idx]
                                
                                from_address = all_addresses[from_idx]
                                to_address = all_addresses[to_idx]
                                
                                segment_url = (
                                    f"https://www.google.com/maps/dir/?api=1"
                                    f"&origin={from_coords[0]},{from_coords[1]}"
                                    f"&destination={to_coords[0]},{to_coords[1]}"
                                    f"&travelmode=driving"
                                )
                                
                                st.markdown(f"[{from_address} → {to_address}]({segment_url})")
                    else:
                        st.warning(f"Nessun dato trovato per il giorno {giorno_selezionato}.")
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
    3. **Premi 'Calcola Tragitto Ottimale'** per vedere il percorso ottimale che inizia da casa, passa per tutti i luoghi di lavoro e torna a casa.
    
    ### Formato del file CSV
    
    Il file CSV deve avere le seguenti colonne:
    - **CASA**: indirizzo completo dell'abitazione
    - **LAVORO**: indirizzo completo del posto di lavoro
    - **GIORNO**: data nel formato GG/MM/AAAA
    
    Esempio:
    ```
    CASA;LAVORO;GIORNO
    Via Roma 1, Milano;Via Dante 15, Milano;01/05/2025
    Via Roma 1, Milano;Via Montenapoleone 8, Milano;01/05/2025
    Via Roma 1, Milano;Piazza Duomo 1, Milano;01/05/2025
    ```
    
    ### Note
    - L'applicazione calcola il percorso ottimale partendo da casa, passando per tutti i luoghi di lavoro e tornando a casa.
    - Per ogni giorno, puoi avere più luoghi di lavoro da visitare.
    - L'applicazione utilizza API gratuite (OpenStreetMap e OSRM) per la geocodifica e il calcolo del percorso.
    """)

# Footer con informazioni
st.markdown("---")
st.markdown("Applicazione creata con Streamlit. Utilizza le API gratuite di OpenStreetMap e OSRM.")
