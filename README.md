# progetto_"come mi vesto?"

Questa repository contiene un algoritmo grado di riconoscere ed abbinare vestiti, valido per il progetto d'esame di Laura De Vita e Duilio Marco. Il modello ha due funzioni distinte:

- utilizzare le reti neurali per classificare i vestiti in in 5 marco categorie con rispettive sottocategorie:
    1. **Giubbini**: blazer, giacca in pelle,  giacchetta, giubbino invernale, giubbino leggero, montgomery;
    2. **magliette**: body, camicia a maniche corte, camicia a maniche lunghe, dolce vita, felpa, maglietta a maniche corte, maglietta a maniche lunghe, pullover, tank top, top;
    3. **pantaloni**: jeans, pantaloncino, pantaloncino, pantalone formale, salopette corta, salopette lunga;
    4. **vestiti**: mini vestito, mini vestito a bretelle, mini vestito a maniche lunghe, vestito da sera, vestito da sera a maniche lunghe, vestito intero, vestito intero a bretelle, vestito intero a maniche lunghe;
    5. **scarpe**: ciabatte, sandali classici, sandali con tacco, scarpe da ginnastica, stivaletti, stivali, stivali con tacco, stivali invernali.
- tramite la fuzzy logic/ un algoritmo evolutivo aiuta l'user a trovare la migiore combinazione di indumenti secondo i seguenti parametri: 
    1. **meteo**: 
    2. **stagione**: 
    3. **stile**;

## Struttura della Repository

L'alorigmo si distingue in nelle seguenti porzioni che operano separatamente:

- **classificatore.py**: che continene il codice relativo alla classificazione degli indumenti. il suo input sarà una qualsisi serie di immagini di vestiti inserite nella cartella "armadio" e il suo output è composto da due file:
    1. *"armadio_classificato.csv"*: esso conterrà 3 colonne, la oprima è il nome della foto, la seconda la categoria in cui è stata classificata e la terza è la sua macro categoria
    2. *"classified_clothes"*: che consiste in un collage delle varie foto dei vestiti con le rispettive categorie e ragguppate nelle rispettive macrocategorie.

- inserisci parte file fuzzy logic / algoritmi evolutivi

- **requirements.txt**: che continene le librerie e le loro versioni che sono state utilizzate.
- **armadio**: è una cartella vuota in cui caricare il proprio file contentente le immagini dei propri vestiti
- **dataset**: è la cartella che costituisce il punto di riferimento del modello, tramite la quale è capace di classificare i vestiti. questo dataset è composta da un file zip contenente 5661 immagini di indumenti e un file csv che contiene i label di ogni immagine. 

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

## Funzionamento

Per eseguire il codice le azioni da seguire, dopo aver setuppato l'ambiente, sono le senguenti:
  1. importare nella cartella armadio le foto dei vestiti
  2. far eseguire il codice contenuto nel file classificatore.py
  3. far eseguire il codice contenuto nel file ----- dopo aver impostato le specifiche desiderate

## Conclusioni
Dunuque, lo scopo di questo algoritmo è facilitare l'utente nella "stressante" scelta dell'abbigliamento da indossare, catalogando l'armadio in sezioni di più semplice consultazione e fornendo combiazioni di indumenti secondo le sue esigenze.