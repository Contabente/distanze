import streamlit as st
import requests
import folium
from folium.features import DivIcon
import polyline
from streamlit_folium import folium_static
import pandas as pd
from datetime import datetime
import json

# Titolo dell'app
st.title("Pianificatore del Tragitto Casa-Lavoro")

# Sidebar per l'inserimento degli indirizzi e la data
with st.sidebar:
    st.header("Impostazioni")
    
    # Inserimento degli indirizzi
    casa_address = st.text_input("Indirizzo di Casa", value="Via Roma 1, Milano")
    lavoro_address = st.text_input("Indirizzo di Lavoro", value="Via Dante 15, Milano")
    
    # Selezione della data
    selected_date = st.date_input("Seleziona il giorno", datetime.now())
    
    # Pulsante per calcolare il percorso
    calculate_button = st.button("Calcola Percorso", type="primary")

# Funzione per convertire indirizzo in coordinate usando Nominatim (OpenStreetMap)
def geocode_address(address):
    try:
        base_url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": address,
            "format": "json",
            "limit": 1,
        }
        headers = {
            "User-Agent": "TraggittoMinimoApp/1.0"  # È buona pratica fornire un User-Agent
        }
        
        response = requests.get(base_url, params=params, headers=headers)
        data = response.json()
        
        if data and len(data) > 0:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            display_name = data[0]["display_name"]
            return lat, lon, display_name
        else:
            st.error(f"Impossibile trovare l'indirizzo: {address}")
            return None, None, None
    except Exception as e:
        st.error(f"Errore durante la geocodifica: {str(e)}")
        return None, None, None

# Funzione per calcolare il percorso usando OSRM
def get_route(start_coords, end_coords):
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{start_coords[1]},{start_coords[0]};{end_coords[1]},{end_coords[0]}?overview=full&geometries=polyline"
        response = requests.get(url)
        data = response.json()
        
        if data["code"] != "Ok":
            st.error("Errore nel calcolo del percorso")
            return None, None
        
        route = data["routes"][0]
        geometry = route["geometry"]
        duration = route["duration"] / 60  # Convertito in minuti
        distance = route["distance"] / 1000  # Convertito in km
        
        # Decodifica la geometria polyline
        decoded_polyline = polyline.decode(geometry)
        
        return decoded_polyline, {"duration": duration, "distance": distance}
    except Exception as e:
        st.error(f"Errore durante il calcolo del percorso: {str(e)}")
        return None, None

# Funzione per visualizzare il percorso sulla mappa
def display_route(casa_coords, lavoro_coords, route_casa_lavoro, route_lavoro_casa, casa_name, lavoro_name, metrics_casa_lavoro, metrics_lavoro_casa):
    # Creare una mappa centrata tra i due punti
    center_lat = (casa_coords[0] + lavoro_coords[0]) / 2
    center_lon = (casa_coords[1] + lavoro_coords[1]) / 2
    my_map = folium.Map(location=[center_lat, center_lon], zoom_start=12)
    
    # Aggiungere marker per casa e lavoro
    folium.Marker(
        location=[casa_coords[0], casa_coords[1]],
        popup=casa_name,
        tooltip="Casa",
        icon=folium.Icon(icon="home", prefix="fa", color="green")
    ).add_to(my_map)
    
    folium.Marker(
        location=[lavoro_coords[0], lavoro_coords[1]],
        popup=lavoro_name,
        tooltip="Lavoro",
        icon=folium.Icon(icon="briefcase", prefix="fa", color="blue")
    ).add_to(my_map)
    
    # Aggiungere il percorso Casa -> Lavoro
    folium.PolyLine(
        route_casa_lavoro,
        color="blue",
        weight=4,
        opacity=0.8,
        tooltip="Casa -> Lavoro"
    ).add_to(my_map)
    
    # Aggiungere il percorso Lavoro -> Casa
    folium.PolyLine(
        route_lavoro_casa,
        color="green",
        weight=4,
        opacity=0.8,
        tooltip="Lavoro -> Casa"
    ).add_to(my_map)
    
    # Aggiungi etichette alle linee
    midpoint_casa_lavoro = route_casa_lavoro[len(route_casa_lavoro) // 2]
    folium.map.Marker(
        location=midpoint_casa_lavoro,
        icon=DivIcon(
            icon_size=(150, 36),
            icon_anchor=(75, 18),
            html=f'<div style="font-size: 12pt; color: blue; text-align: center;">Casa → Lavoro</div>'
        )
    ).add_to(my_map)
    
    midpoint_lavoro_casa = route_lavoro_casa[len(route_lavoro_casa) // 2]
    folium.map.Marker(
        location=midpoint_lavoro_casa,
        icon=DivIcon(
            icon_size=(150, 36),
            icon_anchor=(75, 18),
            html=f'<div style="font-size: 12pt; color: green; text-align: center;">Lavoro → Casa</div>'
        )
    ).add_to(my_map)
    
    return my_map

# Esegui il calcolo quando si preme il pulsante
if calculate_button:
    # Geocodifica degli indirizzi
    casa_lat, casa_lon, casa_display = geocode_address(casa_address)
    lavoro_lat, lavoro_lon, lavoro_display = geocode_address(lavoro_address)
    
    if casa_lat and lavoro_lat:
        casa_coords = (casa_lat, casa_lon)
        lavoro_coords = (lavoro_lat, lavoro_lon)
        
        # Calcola percorsi
        route_casa_lavoro, metrics_casa_lavoro = get_route(casa_coords, lavoro_coords)
        route_lavoro_casa, metrics_lavoro_casa = get_route(lavoro_coords, casa_coords)
        
        if route_casa_lavoro and route_lavoro_casa:
            # Mostra informazioni sul percorso
            st.header(f"Percorso per {selected_date.strftime('%d/%m/%Y')}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Casa → Lavoro")
                st.write(f"Distanza: {metrics_casa_lavoro['distance']:.2f} km")
                st.write(f"Durata: {metrics_casa_lavoro['duration']:.1f} minuti")
            
            with col2:
                st.subheader("Lavoro → Casa")
                st.write(f"Distanza: {metrics_lavoro_casa['distance']:.2f} km")
                st.write(f"Durata: {metrics_lavoro_casa['duration']:.1f} minuti")
            
            st.subheader("Percorso completo")
            st.write(f"Distanza totale: {metrics_casa_lavoro['distance'] + metrics_lavoro_casa['distance']:.2f} km")
            st.write(f"Durata totale: {metrics_casa_lavoro['duration'] + metrics_lavoro_casa['duration']:.1f} minuti")
            
            # Visualizza sulla mappa
            my_map = display_route(
                casa_coords, lavoro_coords, 
                route_casa_lavoro, route_lavoro_casa,
                casa_display, lavoro_display,
                metrics_casa_lavoro, metrics_lavoro_casa
            )
            
            st.subheader("Mappa del percorso")
            folium_static(my_map)
            
            # Tabella riassuntiva
            st.subheader("Riepilogo")
            data = {
                "Percorso": ["Casa → Lavoro", "Lavoro → Casa", "Totale"],
                "Distanza (km)": [
                    f"{metrics_casa_lavoro['distance']:.2f}",
                    f"{metrics_lavoro_casa['distance']:.2f}",
                    f"{metrics_casa_lavoro['distance'] + metrics_lavoro_casa['distance']:.2f}"
                ],
                "Durata (min)": [
                    f"{metrics_casa_lavoro['duration']:.1f}",
                    f"{metrics_lavoro_casa['duration']:.1f}",
                    f"{metrics_casa_lavoro['duration'] + metrics_lavoro_casa['duration']:.1f}"
                ]
            }
            df = pd.DataFrame(data)
            st.table(df)
            
            # Salva le informazioni del tragitto (puoi implementare il salvataggio in un file se necessario)
            saved_info = {
                "data": selected_date.strftime('%Y-%m-%d'),
                "casa": casa_address,
                "lavoro": lavoro_address,
                "distanza_totale": metrics_casa_lavoro['distance'] + metrics_lavoro_casa['distance'],
                "durata_totale": metrics_casa_lavoro['duration'] + metrics_lavoro_casa['duration']
            }
            st.session_state.saved_info = saved_info
        else:
            st.error("Impossibile calcolare i percorsi")
    else:
        st.error("Verifica che gli indirizzi inseriti siano corretti")

# Mostra informazioni sulla modalità d'uso
if not calculate_button:
    st.info("""
    ### Come usare l'app:
    1. Inserisci gli indirizzi di casa e lavoro nella barra laterale
    2. Seleziona la data di interesse
    3. Clicca su 'Calcola Percorso'
    
    L'app calcolerà il tragitto minimo Casa → Lavoro → Casa e mostrerà i dettagli sulla mappa.
    """)
    
    # Esempio di immagine placeholder per la mappa (quando non ci sono ancora dati)
    st.image("https://via.placeholder.com/800x400?text=Inserisci+gli+indirizzi+e+calcola+il+percorso", use_column_width=True)

# Informazioni sul footer
st.markdown("---")
st.markdown("App creata per calcolare il tragitto minimo Casa-Lavoro utilizzando le API gratuite di OpenStreetMap")
