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

    if 'CASA' not in df.columns or 'LAVORO' not in df.columns:
        st.error("Il file CSV deve contenere le colonne 'CASA' e 'LAVORO'.")
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

        def calculate_distance(row):
            casa = casa_coords.get(row['CASA'])
            lavoro = lavoro_coords.get(row['LAVORO'])
            if casa and lavoro:
                return round(geodesic(casa, lavoro).kilometers * 2, 2)
            return None

        df['Distanza_km'] = df.apply(calculate_distance, axis=1)

        st.success("Distanze calcolate con successo!")
        st.dataframe(df)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Scarica risultati in CSV",
            data=csv,
            file_name='distanze_calcolate.csv',
            mime='text/csv'
        )
