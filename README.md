# progetto_esame

Questa repository contiene un algoritmo di machine learning unito ad uno di fuzzy logic in
grado di riconoscere ed abbinare vestiti, valido per il progetto d'esame di Laura De Vita e Duilio Marco. 

Esso è stato scritto da noi e pubblicato su GitHub per essere poi eseguito su un qualsiasi altro dispositivo. 

## Struttura della Repository

La repositoty è organizzata in:

- `codice.py`: che continene il codice dell'algoritmo scritto e testato;
- `requirements.txt`: che continene le librerie e le loro versioni che abbiamo utilizzato;

## Setup Linux/MaxOs

Creare un ambiente Python e installare le dipendenze:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Setup ambiente virtuale (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Poi aprire `codice.py`.

Per mostrare tutte le possibili opzioni:

```bash
python3 onemax_deap.py --help
```

## Output previsto

avremo una classificazione dell'armadio e in base all'esigenze dell'user, delle opzioni di conbinazione di vestiti adeguate.