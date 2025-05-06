import csv
import requests
import time
from itertools import permutations

# URL base per l'API OSRM gratuita
OSRM_URL = "https://router.project-osrm.org/route/v1/driving/"

def geocode_address(address):
    """
    Converte un indirizzo in coordinate geografiche (latitudine, longitudine)
    usando l'API gratuita di OpenStreetMap Nominatim.
    """
    if not address or address.strip() == "":
        return None
        
    try:
        # Rispettiamo le policy di uso della API Nominatim aggiungendo un user-agent
        headers = {
            'User-Agent': 'PythonRouteOptimizer/1.0'
        }
        
        # Formatta l'indirizzo per l'URL
        encoded_address = address.replace(' ', '+')
        url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json&limit=1"
        
        # Facciamo la richiesta
        response = requests.get(url, headers=headers)
        
        # Aggiungiamo un ritardo per rispettare i limiti di utilizzo dell'API
        time.sleep(1)
        
        # Processiamo la risposta
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                print(f"Indirizzo geocodificato: {address} -> ({lat}, {lon})")
                return (lat, lon)
        
        # Se arriviamo qui, c'è stato un problema con la geocodifica
        print(f"Impossibile geocodificare l'indirizzo: {address}")
        return None
        
    except Exception as e:
        print(f"Errore durante la geocodifica: {str(e)}")
        return None

def ottieni_distanza(origine, destinazione):
    """
    Calcola la distanza tra due indirizzi usando l'API gratuita OSRM
    """
    if not origine or not destinazione:
        return float('inf')  # Distanza infinita per indirizzi invalidi
    
    try:
        # Geocodifica gli indirizzi
        print(f"\nCalcolo distanza da {origine} a {destinazione}...")
        origine_coords = geocode_address(origine)
        destinazione_coords = geocode_address(destinazione)
        
        if not origine_coords or not destinazione_coords:
            print("Impossibile ottenere le coordinate per uno degli indirizzi.")
            return float('inf')
        
        # Formato richiesto da OSRM: {lon},{lat}
        origine_str = f"{origine_coords[1]},{origine_coords[0]}"
        destinazione_str = f"{destinazione_coords[1]},{destinazione_coords[0]}"
        
        # Costruisci l'URL per la richiesta all'API OSRM
        url = f"{OSRM_URL}{origine_str};{destinazione_str}?overview=false"
        
        # Effettua la richiesta
        response = requests.get(url)
        
        # Aggiungiamo un piccolo ritardo per rispettare i limiti di utilizzo dell'API
        time.sleep(0.5)
        
        # Verifica ed elabora la risposta
        if response.status_code == 200:
            data = response.json()
            
            # Controlla che ci sia un percorso valido
            if data['code'] == 'Ok' and len(data['routes']) > 0:
                # La distanza è in metri
                distance = data['routes'][0]['distance']
                print(f"Distanza da {origine} a {destinazione}: {distance/1000:.2f} km")
                return distance
        
        # Se arriviamo qui, c'è stato un problema nel calcolo del percorso
        print(f"Impossibile calcolare il percorso tra {origine} e {destinazione}")
        return float('inf')
        
    except Exception as e:
        print(f"Errore durante il calcolo della distanza: {str(e)}")
        return float('inf')

def carica_csv(file_path, separator=';'):
    """Carica i dati dal file CSV"""
    try:
        print(f"Caricamento del file CSV: {file_path}")
        
        dati = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=separator)
            headers = next(reader)  # Leggi l'intestazione
            
            for row in reader:
                if len(row) >= 3:  # Verifichiamo che ci siano almeno 3 colonne
                    dati.append({
                        'CASA': row[0].strip() if row[0].strip() else None,
                        'LAVORO': row[1].strip() if row[1].strip() else None,
                        'GIORNO': row[2].strip() if row[2].strip() else None
                    })
        
        print(f"File caricato con successo. Righe totali: {len(dati)}")
        return dati, headers
    except Exception as e:
        print(f"Errore nel caricamento del file CSV: {str(e)}")
        return None, None

def main():
    # Percorso del file CSV
    file_path = "PROVA2.csv"
    
    # Carica i dati
    dati, headers = carica_csv(file_path)
    if dati is None:
        return
    
    # Chiedi all'utente di selezionare un giorno
    print("\nGiorni disponibili:")
    giorni = set()
    for row in dati:
        if row['GIORNO']:
            giorni.add(row['GIORNO'])
    
    giorni_list = sorted(list(giorni))
    for i, giorno in enumerate(giorni_list):
        print(f"{i+1}. {giorno}")
    
    # Seleziona il giorno
    while True:
        try:
            scelta = int(input("\nSeleziona un giorno (numero): "))
            if 1 <= scelta <= len(giorni_list):
                giorno_selezionato = giorni_list[scelta-1]
                break
            print("Scelta non valida. Riprova.")
        except ValueError:
            print("Inserisci un numero valido.")
    
    print(f"\nCalcolo percorso per il giorno: {giorno_selezionato}")
    
    # Filtra i dati per il giorno selezionato
    dati_giorno = [row for row in dati if row['GIORNO'] == giorno_selezionato]
    
    # Verifica se ci sono indirizzi validi
    dati_validi = [row for row in dati_giorno if row['CASA'] and row['LAVORO']]
    
    if not dati_validi:
        print("Nessun indirizzo valido trovato per questo giorno.")
        return
    
    print(f"Trovati {len(dati_validi)} indirizzi per il giorno {giorno_selezionato}.")
    
    # Ottieni indirizzi unici di casa e lavoro
    indirizzi_casa = list({row['CASA'] for row in dati_validi if row['CASA']})
    indirizzi_lavoro = list({row['LAVORO'] for row in dati_validi if row['LAVORO']})
    
    # Visualizza gli indirizzi trovati
    print("\nIndirizzi CASA:")
    for idx, indirizzo in enumerate(indirizzi_casa):
        print(f"{idx+1}. {indirizzo}")
    
    print("\nIndirizzi LAVORO:")
    for idx, indirizzo in enumerate(indirizzi_lavoro):
        print(f"{idx+1}. {indirizzo}")
    
    # Se c'è un solo indirizzo casa e un solo indirizzo lavoro
    if len(indirizzi_casa) == 1 and len(indirizzi_lavoro) == 1:
        casa = indirizzi_casa[0]
        lavoro = indirizzi_lavoro[0]
        
        print("\nCalcolo distanze tra gli indirizzi...")
        
        distanza_casa_lavoro = ottieni_distanza(casa, lavoro)
        distanza_lavoro_casa = ottieni_distanza(lavoro, casa)
        
        if distanza_casa_lavoro == float('inf') or distanza_lavoro_casa == float('inf'):
            print("\nImpossibile calcolare il percorso completo a causa di errori nella geocodifica o nel routing.")
            return
        
        distanza_totale = distanza_casa_lavoro + distanza_lavoro_casa
        
        print("\nRisultato percorso ottimale:")
        print(f"1. Partenza da CASA: {casa}")
        print(f"2. Arrivo a LAVORO: {lavoro}")
        print(f"3. Ritorno a CASA: {casa}")
        print(f"\nDistanza totale: {distanza_totale/1000:.2f} km")
    else:
        # Se ci sono più indirizzi, calcola il percorso ottimale
        print("\nCalcolo del percorso ottimale con più indirizzi...")
        
        # Creiamo una lista di tutti gli indirizzi
        indirizzi_lavoro_unici = list(set(indirizzi_lavoro))
        casa_base = indirizzi_casa[0]  # Usiamo il primo indirizzo casa come base
        
        print(f"Indirizzo CASA base: {casa_base}")
        print("Calcolo delle distanze tra tutti gli indirizzi...")
        
        # Matrice delle distanze
        distanze = {}
        
        # Calcola distanza da casa a ogni lavoro
        for lavoro in indirizzi_lavoro_unici:
            distanze[(casa_base, lavoro)] = ottieni_distanza(casa_base, lavoro)
            
        # Calcola distanza tra ogni coppia di lavori
        for i, lavoro1 in enumerate(indirizzi_lavoro_unici):
            for lavoro2 in indirizzi_lavoro_unici[i+1:]:
                dist = ottieni_distanza(lavoro1, lavoro2)
                distanze[(lavoro1, lavoro2)] = dist
                distanze[(lavoro2, lavoro1)] = dist
                
        # Calcola distanza da ogni lavoro a casa
        for lavoro in indirizzi_lavoro_unici:
            distanze[(lavoro, casa_base)] = ottieni_distanza(lavoro, casa_base)
        
        # Trova il percorso ottimale usando una semplice implementazione del TSP
        if len(indirizzi_lavoro_unici) <= 6:  # Limita il calcolo del permutazioni per evitare problemi di performance
            print("Calcolo di tutte le possibili combinazioni di percorso...")
            
            # Genera tutte le possibili permutazioni degli indirizzi lavoro
            best_route = None
            min_distance = float('inf')
            
            for perm in permutations(indirizzi_lavoro_unici):
                # Calcola la distanza totale per questo percorso
                route_distance = distanze[(casa_base, perm[0])]  # Da casa al primo lavoro
                
                # Tra i lavori
                for i in range(len(perm) - 1):
                    route_distance += distanze[(perm[i], perm[i+1])]
                
                # Dall'ultimo lavoro a casa
                route_distance += distanze[(perm[-1], casa_base)]
                
                # Aggiorna il miglior percorso se questo è migliore
                if route_distance < min_distance:
                    min_distance = route_distance
                    best_route = perm
            
            # Mostra il percorso ottimale
            if best_route:
                print("\nPercorso ottimale trovato:")
                print(f"1. Partenza da CASA: {casa_base}")
                
                for i, lavoro in enumerate(best_route):
                    print(f"{i+2}. Visita a LAVORO: {lavoro}")
                
                print(f"{len(best_route)+2}. Ritorno a CASA: {casa_base}")
                print(f"\nDistanza totale: {min_distance/1000:.2f} km")
            else:
                print("Impossibile trovare un percorso valido.")
        else:
            print("Troppe località da visitare per calcolare tutte le permutazioni.")
            print("Per ottimizzare percorsi con molte destinazioni, si consiglia di implementare algoritmi più efficienti come nearest neighbor o branch-and-bound.")

if __name__ == "__main__":
    main()
