# progetto_"come mi vesto?"

Questa repository contiene un algoritmo grado di riconoscere ed abbinare vestiti, valido per il progetto d'esame di De Vita Laura e Duilio Marco. Il modello ha due funzioni distinte:

- Utilizzare le reti neurali per classificare i vestiti in 5 macro categorie con rispettive sottocategorie:
    1. **Giubbini**: blazer, giacca in pelle,  giacchetta, giubbino invernale, giubbino leggero, montgomery;
    2. **magliette**: body, camicia a maniche corte, camicia a maniche lunghe, dolce vita, felpa, maglietta a maniche corte, maglietta a maniche lunghe, pullover, tank top, top;
    3. **pantaloni**: jeans, pantaloncino, pantaloncino, pantalone formale, salopette corta, salopette lunga;
    4. **vestiti**: mini vestito, mini vestito a bretelle, mini vestito a maniche lunghe, vestito da sera, vestito da sera a maniche lunghe, vestito intero, vestito intero a bretelle, vestito intero a maniche lunghe;
    5. **scarpe**: ciabatte, sandali classici, sandali con tacco, scarpe da ginnastica, stivaletti, stivali, stivali con tacco, stivali invernali.
- Aiutare, tramite un algoritmo evolutivo, l'user a trovare la migiore combinazione di indumenti secondo i seguenti parametri: 
    1. **meteo**: soleggiato, ventoso, piovoso, nevoso e nuvoloso;
    2. **stagione**: inverno, primavera, estate e autunno;
    3. **stile**; professionale, smart casual,  casual, elegante, sportivo e glamour 

## Struttura della Repository

L'alorigmo è composto dalle seguenti seguenti porzioni:

- **classificatore.py**: che continene il codice relativo alla classificazione degli indumenti. Il suo input sarà una serie di immagini di vestiti inserite nella cartella "armadio" e il suo output è composto da due file:
    1. *"armadio_classificato.csv"*: esso conterrà 3 colonne, la prima è il nome della foto, la seconda la categoria in cui è stata classificata e la terza è la sua macro categoria
    2. *"classified_clothes"*: che consiste in un collage delle varie foto dei vestiti con le rispettive categorie e ragguppate nelle rispettive macrocategorie.
- **stilista.py**: che contiene il codice relativo al creare combinazioni di indumenti ottimali. I sui input saranno: il file l'armadio classificato dal classificatore e le informazioni relative alle esigenze dell'utente. Mentre l'output sarà un file contenente i 3 outfit migliori trovati sia per i vestiti che per la combinazione maglietta + pantalone.
- **requirements.txt**: che continene le librerie e le loro versioni che sono state utilizzate.
- **armadio**: è una cartella in cui caricare il  file contentente le immagini dei vestiti. 
- **dataset**: è la cartella che costituisce il punto di riferimento del modello, tramite la quale è capace di classificare i vestiti. È composta da un file zip contenente 5661 immagini di indumenti, un file csv che contiene i label di ogni immagine e un'altro file cvs dove a ogni label è associato un certo punteggio in base ai parametri scritti sopra (meteo, stagione, stile)

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

Se PowerShell blocca l'attivazione con un errore di Execution Policy, usare il comando: 

```Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass```

e poi ripetere:

```.\.venv\Scripts\Activate.ps1```

## Funzionamento

Per eseguire il codice le azioni da seguire, dopo aver setuppato l'ambiente, sono le senguenti:
  1. importare nella cartella armadio le foto dei vestiti. Il file contenente le foto andrà chiamato "armadio_n", con n un qualsiasi numero intero.
  2. far eseguire il codice contenuto nel file classificatore.py
  3. far eseguire il codice contenuto nel file stilista.py dopo aver impostato le specifiche desiderate

Per testare l'algoritmo sono stati messi a disposizione 3 "armadi" di prova diversi. Ogni run dell'algorritmo salva i dati ottenuti per ogni armadio su cui viene utilizzato, ma in caso si utilizzi su un armadio su cui è gia stato applicato, il file precedente verrà sovrascritto. 

## Conclusioni

Lo scopo di questo algoritmo è facilitare l'utente nella "stressante" scelta dell'abbigliamento da indossare, catalogando l'armadio in sezioni di più semplice consultazione e fornendo combiazioni di indumenti secondo le sue esigenze.