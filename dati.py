import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

def calcola_combinazione_fuzzy(stagione_input, meteo_input, stile_input):
    # 1. DEFINIZIONE DEGLI INPUT E OUTPUT
    # Stagione (Scala da 0 a 3: Estate=0, Primavera=1, Autunno=2, Inverno=3)
    stagione = ctrl.Antecedent(np.arange(0, 4, 1), 'stagione')
    
    # Meteo (Scala da 0 a 3: Sole=0, Vento=1, Pioggia=2, Neve=3)
    meteo = ctrl.Antecedent(np.arange(0, 4, 1), 'meteo')
    
    # Stile (da 0 = casual a 10 = elegante)
    stile = ctrl.Antecedent(np.arange(0, 11, 1), 'stile')

    # Output del sistema (rimangono invariati)
    pesantezza = ctrl.Consequent(np.arange(0, 11, 1), 'pesantezza')
    formalita = ctrl.Consequent(np.arange(0, 11, 1), 'formalita')

    # 2. FUNZIONI DI APPARTENENZA (Fuzzificazione)
    
    # --- MODIFICA: Nuove funzioni per la Stagione (scala 0-3) ---
    # Centriamo il picco (il numero centrale) sul valore esatto della stagione
    stagione['estate'] = fuzz.trimf(stagione.universe, [0, 0, 1])
    stagione['primavera'] = fuzz.trimf(stagione.universe, [0, 1, 2])
    stagione['autunno'] = fuzz.trimf(stagione.universe, [1, 2, 3])
    stagione['inverno'] = fuzz.trimf(stagione.universe, [2, 3, 3])

    # --- MODIFICA: Nuove funzioni per il Meteo (scala 0-3) ---
    meteo['sole'] = fuzz.trimf(meteo.universe, [0, 0, 1])
    meteo['vento'] = fuzz.trimf(meteo.universe, [0, 1, 2])
    meteo['piovoso'] = fuzz.trimf(meteo.universe, [1, 2, 3])
    meteo['nevoso'] = fuzz.trimf(meteo.universe, [2, 3, 3])

    # Funzioni per lo Stile (Invariate)
    stile['casual'] = fuzz.trimf(stile.universe, [0, 0, 5])
    stile['professionale'] = fuzz.trimf(stile.universe, [4, 6, 8])
    stile['elegante'] = fuzz.trimf(stile.universe, [7, 10, 10])

    # Output: Pesantezza dell'abito (Invariate)
    pesantezza['leggero'] = fuzz.trimf(pesantezza.universe, [0, 0, 5])
    pesantezza['medio'] = fuzz.trimf(pesantezza.universe, [3, 5, 7])
    pesantezza['pesante'] = fuzz.trimf(pesantezza.universe, [6, 10, 10])

    # Output: Formalità dell'abito (Invariate)
    formalita['bassa'] = fuzz.trimf(formalita.universe, [0, 0, 5])
    formalita['media'] = fuzz.trimf(formalita.universe, [4, 6, 8])
    formalita['alta'] = fuzz.trimf(formalita.universe, [7, 10, 10])

    # 3. REGOLE FUZZY (Rimangono logicamente identiche)
    regola1 = ctrl.Rule(stagione['inverno'] | meteo['nevoso'], pesantezza['pesante'])
    regola2 = ctrl.Rule(stagione['estate'] & meteo['sole'], pesantezza['leggero'])
    regola3 = ctrl.Rule(stagione['primavera'] | stagione['autunno'], pesantezza['medio'])
    regola4 = ctrl.Rule(stagione['autunno'] & meteo['piovoso'], pesantezza['pesante'])
    regola5 = ctrl.Rule(stagione['estate'] & meteo['vento'], pesantezza['medio'])

    regola6 = ctrl.Rule(stile['casual'], formalita['bassa'])
    regola7 = ctrl.Rule(stile['professionale'], formalita['media'])
    regola8 = ctrl.Rule(stile['elegante'], formalita['alta'])

    # 4. CREAZIONE E SIMULAZIONE DEL SISTEMA
    sistema_controllo = ctrl.ControlSystem([regola1, regola2, regola3, regola4, regola5, regola6, regola7, regola8])
    simulatore = ctrl.ControlSystemSimulation(sistema_controllo)

    # Inserimento dati
    simulatore.input['stagione'] = stagione_input
    simulatore.input['meteo'] = meteo_input
    simulatore.input['stile'] = stile_input

    # Calcolo dei punteggi target
    simulatore.compute()
    
    return simulatore.output['pesantezza'], simulatore.output['formalita']


# === ESEMPIO INTERATTIVO DI UTILIZZO ===

# --- MODIFICA: Dizionari aggiornati per rispettare i valori 0-3 ---
dizionario_stagioni = {
    'estate': 0,
    'primavera': 1,
    'autunno': 2,
    'inverno': 3
}

dizionario_meteo = {
    'sole': 0,
    'vento': 1,
    'pioggia': 2,
    'neve': 3
}

# Input simulati dell'utente
input_utente_stagione = 'autunno'  # estate, primavera, autunno, inverno
input_utente_meteo = 'pioggia'     # sole, vento, pioggia, neve
input_utente_stile = 8             # Stile elegante/professionale (scala 0-10)

# Conversione testuale -> numerica (con valori di default sicuri: 0 per entrambi)
stagione_numerica = dizionario_stagioni.get(input_utente_stagione, 0)
meteo_numerico = dizionario_meteo.get(input_utente_meteo, 0)

# Esecuzione dell'algoritmo
punteggio_pesantezza, punteggio_formalita = calcola_combinazione_fuzzy(
    stagione_numerica, 
    meteo_numerico, 
    input_utente_stile
)

print(f"Input: {input_utente_stagione.capitalize()} con {input_utente_meteo} (Stile: {input_utente_stile}/10)")
print(f"Risultato Fuzzy -> Cerca abiti con Pesantezza: {punteggio_pesantezza:.2f}/10 e Formalità: {punteggio_formalita:.2f}/10")