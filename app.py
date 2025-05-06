import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.distance import geodesic

st.set_page_config(page_title="Calcolo Distanze Casa-Lavoro", layout="centered")
st.title("Calcolo Distanze Casa → Lavoro → Casa")

uploaded_file = st.file_uploader("Carica un file CSV con colonne 'CASA', 'LAVORO' e 'GIORNO'", type="csv")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, sep=';', engine='python')
    except Exception:
        df = pd.read_csv(uploaded_file)

    if 'CASA' not in df.columns or 'LAVORO' not in df.columns or 'GIORNO' not in df.columns:
        st.error("Il file CSV deve contenere le colonne 'CASA', 'LAVORO' e 'GIORNO'.")
    else:
        df['CASA'] = df['CASA'].fillna(method='ffill')

        geolocator = Nominatim(user_agent="distance_calculator")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

        @st.cache_data(show_spinner=False)
        def geocode_addresses(addresses):
            coords = {}
            for address in addresses:
                if pd.isna(address):
                    coords[address] = None
                    continue
                try:
                    location = geocode(address)
                    if location:
                        coords[address] = (location.latitude, location.longitude)
                    else:
                        coords[address] = None
                except Exception:
                    coords[address] = None
            return coords

        st.write("Geocodifica indirizzi...")
        casa_coords = geocode_addresses(df['CASA'].dropna().unique())
        lavoro_coords = geocode_addresses(df['LAVORO'].dropna().unique())

        def calculate_total_distance(group):
            casa_address = group['CASA'].iloc[0]
            casa = casa_coords.get(casa_address)
            lavori = group['LAVORO'].tolist()
            dist = 0
            percorso = [casa]  # Inizia da casa

            # Aggiunge le coordinate di ogni lavoro se valide, evitando duplicati consecutivi
            last_coord = None
            for l in lavori:
                coord = lavoro_coords.get(l)
                if coord and coord != last_coord:
                    percorso.append(coord)
                    last_coord = coord

            if last_coord != casa:
                percorso.append(casa)  # Ritorno a casa solo se l'ultimo indirizzo è diverso

            # Calcola la distanza totale tra punti consecutivi nel percorso
            for i in range(len(percorso) - 1):
                if percorso[i] and percorso[i + 1]:
                    dist += geodesic(percorso[i], percorso[i + 1]).kilometers

            return dist

        distanza_per_giorno = df.groupby('GIORNO').apply(calculate_total_distance).reset_index(name='Distanza_km')
        distanza_per_giorno['Distanza_km'] = distanza_per_giorno['Distanza_km'].round(2)

        st.success("Distanze calcolate con successo!")
        st.dataframe(distanza_per_giorno)

        csv = distanza_per_giorno.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Scarica risultati in CSV",
            data=csv,
            file_name='distanze_per_giorno.csv',
            mime='text/csv'
        )
