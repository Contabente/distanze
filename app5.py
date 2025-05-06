import csv
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import pandas as pd
from itertools import permutations
import json
import time

class AppPercorsoOttimale:
    def __init__(self, root):
        self.root = root
        self.root.title("Calcolo Percorso Ottimale")
        self.root.geometry("800x600")
        
        # Variabili per memorizzare i dati
        self.dati_csv = None
        self.giorni_disponibili = []
        # URL base per l'API OSRM gratuita
        self.osrm_url = "https://router.project-osrm.org/route/v1/driving/"
        
        # Frame principale
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Titolo
        ttk.Label(main_frame, text="Calcolo del Percorso Ottimale", font=("Arial", 16)).pack(pady=10)
        
        # Frame per la selezione del file e del giorno
        select_frame = ttk.LabelFrame(main_frame, text="Selezione dati", padding="10")
        select_frame.pack(fill="x", padx=10, pady=10)
        
        # Caricamento dati
        ttk.Button(select_frame, text="Carica Dati CSV", command=self.carica_dati).grid(row=0, column=0, padx=5, pady=5)
        
        # Selezione del giorno
        ttk.Label(select_frame, text="Seleziona Giorno:").grid(row=0, column=1, padx=5, pady=5)
        self.combo_giorni = ttk.Combobox(select_frame, state="readonly")
        self.combo_giorni.grid(row=0, column=2, padx=5, pady=5)
        
        # Pulsante per calcolare il percorso
        ttk.Button(select_frame, text="Calcola Percorso", command=self.calcola_percorso).grid(row=0, column=3, padx=5, pady=5)
        
        # Frame per i risultati
        result_frame = ttk.LabelFrame(main_frame, text="Risultati", padding="10")
        result_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Area di testo per i risultati
        self.result_text = tk.Text(result_frame, wrap="word", height=15)
        self.result_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbar per l'area di testo
        scrollbar = ttk.Scrollbar(self.result_text, orient="vertical", command=self.result_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.result_text.configure(yscrollcommand=scrollbar.set)
        
        # Frame per la mappa (placeholder)
        map_frame = ttk.LabelFrame(main_frame, text="Mappa", padding="10")
        map_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ttk.Label(map_frame, text="La visualizzazione della mappa richiede l'integrazione con API come Google Maps").pack(pady=20)
        
        # Caricamento automatico del file CSV fornito
        self.carica_csv_fornito()
    
    def carica_csv_fornito(self):
        """Carica il file CSV fornito"""
        try:
            # Carica il file CSV fornito
            self.dati_csv = pd.read_csv("PROVA2.csv", sep=";")
            self.aggiorna_giorni_disponibili()
            self.result_text.insert("1.0", "File CSV caricato con successo.\n")
            self.result_text.insert("end", f"Righe totali: {len(self.dati_csv)}\n")
            self.mostra_dati_csv()
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile caricare il file CSV: {str(e)}")
    
    def carica_dati(self):
        """Carica i dati da un file CSV selezionato dall'utente"""
        try:
            # Usa un file dialog per selezionare il file CSV
            file_path = filedialog.askopenfilename(
                title="Seleziona file CSV",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            # Se l'utente ha annullato, esci dalla funzione
            if not file_path:
                return
                
            # Carica il file selezionato
            self.dati_csv = pd.read_csv(file_path, sep=";")
            self.aggiorna_giorni_disponibili()
            self.result_text.delete("1.0", "end")
            self.result_text.insert("1.0", f"File CSV caricato con successo: {file_path}\n")
            self.result_text.insert("end", f"Righe totali: {len(self.dati_csv)}\n")
            self.mostra_dati_csv()
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile caricare il file CSV: {str(e)}")
    
    def aggiorna_giorni_disponibili(self):
        """Aggiorna l'elenco dei giorni disponibili nel combobox"""
        if self.dati_csv is not None:
            # Estrai i giorni unici
            self.giorni_disponibili = self.dati_csv['GIORNO'].unique().tolist()
            self.combo_giorni['values'] = self.giorni_disponibili
            if self.giorni_disponibili:
                self.combo_giorni.current(0)  # Seleziona il primo giorno
    
    def mostra_dati_csv(self):
        """Mostra i dati del CSV nella casella di testo dei risultati"""
        if self.dati_csv is not None:
            self.result_text.insert("end", "\nDati disponibili nel CSV:\n")
            self.result_text.insert("end", "-" * 60 + "\n")
            self.result_text.insert("end", self.dati_csv.to_string(index=False) + "\n")
            self.result_text.insert("end", "-" * 60 + "\n")
    
    def geocode_address(self, address):
        """
        Converte un indirizzo in coordinate geografiche (latitudine, longitudine)
        usando l'API gratuita di OpenStreetMap Nominatim.
        """
        if not address or pd.isna(address):
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
                    return (lat, lon)
            
            # Se arriviamo qui, c'è stato un problema con la geocodifica
            self.result_text.insert("end", f"Impossibile geocodificare l'indirizzo: {address}\n")
            return None
            
        except Exception as e:
            self.result_text.insert("end", f"Errore durante la geocodifica: {str(e)}\n")
            return None
    
    def ottieni_distanza(self, origine, destinazione):
        """
        Calcola la distanza tra due indirizzi usando l'API gratuita OSRM
        """
        if not origine or not destinazione or pd.isna(origine) or pd.isna(destinazione):
            return float('inf')  # Distanza infinita per indirizzi invalidi
        
        try:
            # Geocodifica gli indirizzi
            origine_coords = self.geocode_address(origine)
            destinazione_coords = self.geocode_address(destinazione)
            
            if not origine_coords or not destinazione_coords:
                self.result_text.insert("end", "Impossibile ottenere le coordinate per uno degli indirizzi.\n")
                return float('inf')
            
            # Formato richiesto da OSRM: {lon},{lat}
            origine_str = f"{origine_coords[1]},{origine_coords[0]}"
            destinazione_str = f"{destinazione_coords[1]},{destinazione_coords[0]}"
            
            # Costruisci l'URL per la richiesta all'API OSRM
            url = f"{self.osrm_url}{origine_str};{destinazione_str}?overview=false"
            
            # Effettua la richiesta
            response = requests.get(url)
            
            # Aggiungiamo un piccolo ritardo per rispettare i limiti di utilizzo dell'API
            time.sleep(0.5)
            
            # Verifica ed elabora la risposta
            if response.status_code == 200:
                data = response.json()
                
                # Controlla che ci sia un percorso valido
                if data['code'] == 'Ok' and len(data['routes']) > 0:
                    # La distanza è in metri, la convertiamo in km
                    distance = data['routes'][0]['distance']
                    self.result_text.insert("end", f"Distanza da {origine} a {destinazione}: {distance/1000:.2f} km\n")
                    return distance
            
            # Se arriviamo qui, c'è stato un problema nel calcolo del percorso
            self.result_text.insert("end", f"Impossibile calcolare il percorso tra {origine} e {destinazione}\n")
            return float('inf')
            
        except Exception as e:
            self.result_text.insert("end", f"Errore durante il calcolo della distanza: {str(e)}\n")
            return float('inf')
    
    def calcola_percorso(self):
        """Calcola il percorso ottimale per il giorno selezionato"""
        if self.dati_csv is None:
            messagebox.showwarning("Attenzione", "Devi prima caricare i dati CSV")
            return
        
        giorno_selezionato = self.combo_giorni.get()
        if not giorno_selezionato:
            messagebox.showwarning("Attenzione", "Seleziona un giorno")
            return
        
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", f"Calcolo percorso per il giorno: {giorno_selezionato}\n\n")
        
        # Filtra i dati per il giorno selezionato
        dati_giorno = self.dati_csv[self.dati_csv['GIORNO'] == giorno_selezionato]
        
        # Verifica se ci sono indirizzi validi
        dati_giorno = dati_giorno.dropna(subset=['CASA', 'LAVORO'])
        
        if dati_giorno.empty:
            self.result_text.insert("end", "Nessun indirizzo valido trovato per questo giorno.\n")
            return
        
        self.result_text.insert("end", f"Trovati {len(dati_giorno)} indirizzi per il giorno {giorno_selezionato}.\n\n")
        
        # Ottieni indirizzi unici di casa e lavoro
        indirizzi_casa = dati_giorno['CASA'].unique().tolist()
        indirizzi_casa = [indirizzo for indirizzo in indirizzi_casa if isinstance(indirizzo, str) and indirizzo.strip()]
        
        indirizzi_lavoro = dati_giorno['LAVORO'].unique().tolist()
        indirizzi_lavoro = [indirizzo for indirizzo in indirizzi_lavoro if isinstance(indirizzo, str) and indirizzo.strip()]
        
        if not indirizzi_casa:
            self.result_text.insert("end", "Nessun indirizzo CASA valido trovato.\n")
            return
            
        if not indirizzi_lavoro:
            self.result_text.insert("end", "Nessun indirizzo LAVORO valido trovato.\n")
            return
        
        # Visualizza gli indirizzi trovati
        self.result_text.insert("end", "Indirizzi CASA:\n")
        for idx, indirizzo in enumerate(indirizzi_casa):
            self.result_text.insert("end", f"{idx+1}. {indirizzo}\n")
        
        self.result_text.insert("end", "\nIndirizzi LAVORO:\n")
        for idx, indirizzo in enumerate(indirizzi_lavoro):
            self.result_text.insert("end", f"{idx+1}. {indirizzo}\n")
        
        # Se c'è un solo indirizzo casa e un solo indirizzo lavoro
        if len(indirizzi_casa) == 1 and len(indirizzi_lavoro) == 1:
            casa = indirizzi_casa[0]
            lavoro = indirizzi_lavoro[0]
            
            self.result_text.insert("end", "\nCalcolo distanze tra gli indirizzi...\n")
            
            distanza_casa_lavoro = self.ottieni_distanza(casa, lavoro)
            distanza_lavoro_casa = self.ottieni_distanza(lavoro, casa)
            
            if distanza_casa_lavoro == float('inf') or distanza_lavoro_casa == float('inf'):
                self.result_text.insert("end", "\nImpossibile calcolare il percorso completo a causa di errori nella geocodifica o nel routing.\n")
                return
            
            distanza_totale = distanza_casa_lavoro + distanza_lavoro_casa
            
            self.result_text.insert("end", "\nRisultato percorso ottimale:\n")
            self.result_text.insert("end", f"1. Partenza da CASA: {casa}\n")
            self.result_text.insert("end", f"2. Arrivo a LAVORO: {lavoro}\n")
            self.result_text.insert("end", f"3. Ritorno a CASA: {casa}\n")
            self.result_text.insert("end", f"\nDistanza totale: {distanza_totale/1000:.2f} km\n")
        else:
            # Se ci sono più indirizzi, calcola il percorso ottimale
            self.result_text.insert("end", "\nCalcolo del percorso ottimale con più indirizzi...\n")
            
            # Creiamo una lista di tutti gli indirizzi
            indirizzi_lavoro_unici = list(set(indirizzi_lavoro))
            casa_base = indirizzi_casa[0]  # Usiamo il primo indirizzo casa come base
            
            self.result_text.insert("end", f"Indirizzo CASA base: {casa_base}\n")
            self.result_text.insert("end", "Calcolo delle distanze tra tutti gli indirizzi...\n")
            
            # Matrice delle distanze
            distanze = {}
            
            # Calcola distanza da casa a ogni lavoro
            for lavoro in indirizzi_lavoro_unici:
                distanze[(casa_base, lavoro)] = self.ottieni_distanza(casa_base, lavoro)
                
            # Calcola distanza tra ogni coppia di lavori
            for i, lavoro1 in enumerate(indirizzi_lavoro_unici):
                for lavoro2 in indirizzi_lavoro_unici[i+1:]:
                    dist = self.ottieni_distanza(lavoro1, lavoro2)
                    distanze[(lavoro1, lavoro2)] = dist
                    distanze[(lavoro2, lavoro1)] = dist
                    
            # Calcola distanza da ogni lavoro a casa
            for lavoro in indirizzi_lavoro_unici:
                distanze[(lavoro, casa_base)] = self.ottieni_distanza(lavoro, casa_base)
            
            # Trova il percorso ottimale usando una semplice implementazione del TSP
            if len(indirizzi_lavoro_unici) <= 6:  # Limita il calcolo del permutazioni per evitare problemi di performance
                self.result_text.insert("end", "Calcolo di tutte le possibili combinazioni di percorso...\n")
                
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
                    self.result_text.insert("end", "\nPercorso ottimale trovato:\n")
                    self.result_text.insert("end", f"1. Partenza da CASA: {casa_base}\n")
                    
                    for i, lavoro in enumerate(best_route):
                        self.result_text.insert("end", f"{i+2}. Visita a LAVORO: {lavoro}\n")
                    
                    self.result_text.insert("end", f"{len(best_route)+2}. Ritorno a CASA: {casa_base}\n")
                    self.result_text.insert("end", f"\nDistanza totale: {min_distance/1000:.2f} km\n")
                else:
                    self.result_text.insert("end", "Impossibile trovare un percorso valido.\n")
            else:
                self.result_text.insert("end", "Troppe località da visitare per calcolare tutte le permutazioni.\n")
                self.result_text.insert("end", "Per ottimizzare percorsi con molte destinazioni, si consiglia di implementare algoritmi più efficienti come nearest neighbor o branch-and-bound.\n")

def main():
    root = tk.Tk()
    app = AppPercorsoOttimale(root)
    root.mainloop()

if __name__ == "__main__":
    main()
