import random
from dataclasses import dataclass
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import pandas as pd
from deap import base, creator, tools
from PIL import Image

# in questa porzione vengono definiti i percorsi principali e le opzioni disponibili per i parametri utente.
SCORE_FILE = Path("dataset") / "punteggi categorie.csv"
OUTPUT_DIR = Path("risultati outfit")

METEO_OPTIONS = ["soleggiato", "ventoso", "piovoso", "nevoso", "nuvoloso"]
STAGIONE_OPTIONS = ["inverno", "primavera", "estate", "autunno"]
STILE_OPTIONS = ["professionale", "smart casual", "casual", "elegante", "sportivo", "glamour"]


@dataclass
class Garment:
    filename: str
    label: str
    macro: str


# normalizza il testo in minuscolo e senza spazi iniziali/finali per evitare mismatch nei confronti.
def normalize_text(value):
    return str(value).strip().lower()


# converte le macroetichette in un set standard usato internamente dall'algoritmo.
def normalize_macro(value):
    v = normalize_text(value)
    if v.startswith("giubb"):
        return "giubbini"
    if v.startswith("magli"):
        return "magliette"
    if v.startswith("pantal"):
        return "pantaloni"
    if v.startswith("vestit"):
        return "vestiti"
    if v.startswith("scarp"):
        return "scarpe"
    return v

# cerca tutti i csv classificati prodotti dal classificatore, escludendo il file punteggi.
def find_classified_files(root=Path(".")):
    files = []
    for path in root.rglob("* classificato.csv"):
        if "punteggi categorie" in normalize_text(path.name):
            continue
        files.append(path)
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files

# mostra una lista numerata dei file classificati e permette all'utente di selezionare quello da usare.
def choose_classified_file():
    candidates = find_classified_files()
    if not candidates:
        raise FileNotFoundError(
            "Nessun file classificato trovato. Esegui prima classificatore.py."
        )

    print("File classificati trovati:")
    for i, path in enumerate(candidates, start=1):
        print(f"{i}. {path}")

    while True:
        choice = input("Seleziona il file classificato (numero): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(candidates):
            return candidates[int(choice) - 1]
        print("Scelta non valida.")

# crea una cartella output dedicata al singolo armadio.
def build_output_dir_for_classified(classified_csv_path, base_output_dir=OUTPUT_DIR):
    armadio_name = classified_csv_path.stem.replace(" classificato", "").strip()
    if not armadio_name:
        armadio_name = "generico"
    return Path(f"{base_output_dir} {armadio_name}")

# carica la tabella dei punteggi per meteo, stagione e stile e usa file_name come indice.
def load_score_table(score_path=SCORE_FILE):
    if not score_path.exists():
        raise FileNotFoundError(f"File punteggi non trovato: {score_path}")

    df = pd.read_csv(score_path)
    df.columns = [c.strip() for c in df.columns]
    if "file_name" not in df.columns:
        raise ValueError("Il file punteggi deve avere la colonna 'file_name'.")

    df["file_name"] = df["file_name"].astype(str).str.strip().str.lower()
    df = df.set_index("file_name")

    return df

 # carica i capi classificati e li raggruppa per macro-categoria.
def load_classified_wardrobe(classified_csv_path):
    if not classified_csv_path.exists():
        raise FileNotFoundError(f"File classificato non trovato: {classified_csv_path}")

    df = pd.read_csv(classified_csv_path)
    required = {"filename", "label", "macroetichetta"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Il file classificato deve contenere le colonne {sorted(required)}. Mancano: {sorted(missing)}"
        )

    garments = {
        "giubbini": [],
        "magliette": [],
        "pantaloni": [],
        "vestiti": [],
        "scarpe": [],
    }

    for _, row in df.iterrows():
        macro = normalize_macro(row["macroetichetta"])
        if macro in garments:
            garments[macro].append(
                Garment(
                    filename=str(row["filename"]),
                    label=normalize_text(row["label"]),
                    macro=macro,
                )
            )

    return garments

# mostra un prompt con opzioni numerate e restituisce l'opzione selezionata dall'utente.

def ask_choice(prompt, options):
    print(prompt)
    for i, option in enumerate(options, start=1):
        print(f"{i}. {option}")

    while True:
        choice = input("Inserisci numero: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print("Scelta non valida.")

# verifica che esistano abbastanza capi per costruire outfit validi secondo i vincoli richiesti.
def check_feasibility(wardrobe, stagione, stile):
    if len(wardrobe["scarpe"]) == 0:
        raise ValueError("Nessuna scarpa disponibile nel file classificato.")

    if stagione != "estate" and len(wardrobe["giubbini"]) == 0:
        raise ValueError("Manca almeno un giubbino: richiesto fuori dall'estate.")

    if stile == "sportivo":
        if len(wardrobe["pantaloni"]) == 0:
            raise ValueError("Con stile sportivo serve almeno un pantalone disponibile.")
        if len(wardrobe["magliette"]) == 0:
            raise ValueError("Con stile sportivo serve almeno una maglietta disponibile.")
    else:
        if len(wardrobe["magliette"]) == 0 and len(wardrobe["vestiti"]) == 0:
            raise ValueError("Servono magliette o vestiti per creare outfit validi.")
        if len(wardrobe["magliette"]) > 0 and len(wardrobe["pantaloni"]) == 0 and len(wardrobe["vestiti"]) == 0:
            raise ValueError("Mancano i pantaloni e non ci sono vestiti disponibili.")

# calcola il punteggio di un capo come somma dei valori su meteo, stagione e stile scelti.
def item_score(score_df, garment_label, meteo, stagione, stile):
    if garment_label not in score_df.index:
        return 0.0

    row = score_df.loc[garment_label]
    columns = [meteo, stagione, stile]
    total = 0.0
    for col in columns:
        if col in row.index:
            total += float(row[col])
    return total

# traduce una soluzione generata dall'algoritmo in un outfit reale rispettando i vincoli impostati.
def decode_individual(individual, wardrobe, stagione, stile):
    use_dress = int(individual[0]) == 1

    if stile == "sportivo":
        use_dress = False

    if use_dress and len(wardrobe["vestiti"]) == 0:
        use_dress = False
    if (not use_dress) and len(wardrobe["magliette"]) == 0 and len(wardrobe["vestiti"]) > 0 and stile != "sportivo":
        use_dress = True
    if (not use_dress) and len(wardrobe["pantaloni"]) == 0 and len(wardrobe["vestiti"]) > 0:
        use_dress = True

    if use_dress:
        upper_list = wardrobe["vestiti"]
        outfit_type = "vestito"
    else:
        upper_list = wardrobe["magliette"]
        outfit_type = "maglietta"

    giubbino = None
    if stagione != "estate":
        giubbino = wardrobe["giubbini"][individual[1] % len(wardrobe["giubbini"])]

    upper = upper_list[individual[2] % len(upper_list)]
    pantalone = None
    if not use_dress:
        pantalone = wardrobe["pantaloni"][individual[3] % len(wardrobe["pantaloni"])]
    scarpa = wardrobe["scarpe"][individual[4] % len(wardrobe["scarpe"])]

    return {
        "tipo_outfit": outfit_type,
        "giubbino": giubbino,
        "upper": upper,
        "pantalone": pantalone,
        "scarpa": scarpa,
    }

#fa si che ogni outfit sia unico.
def individual_signature(decoded):
    giubbino_name = decoded["giubbino"].filename if decoded["giubbino"] is not None else "NO_GIUBBINO"
    pantalone_name = decoded["pantalone"].filename if decoded["pantalone"] is not None else "NO_PANTALONE"
    return (
        decoded["tipo_outfit"],
        giubbino_name,
        decoded["upper"].filename,
        pantalone_name,
        decoded["scarpa"].filename,
    )

 # stampa una barra di caricamento per monitorare il processo di generazione di soluzioni
 # generazione per generazione 
def print_progress_bar(current, total):
    width = 34
    ratio = current / total
    filled = int(width * ratio)
    bar = "#" * filled + "-" * (width - filled)
    print(f"\rRicerca evolutiva: [{bar}] {current}/{total} generazioni", end="", flush=True)

# genera il grafico dell'andamento fitness.
def plot_evolution(history_max, history_avg, output_dir):
    x = list(range(1, len(history_max) + 1))
    plt.figure(figsize=(10, 5))
    plt.plot(x, history_max, "-o", label="Best fitness")
    plt.plot(x, history_avg, "--o", label="Average fitness")
    plt.xlabel("Generazione")
    plt.ylabel("Fitness")
    plt.title("Andamento ricerca soluzioni ottimali")
    plt.grid(True, alpha=0.3)
    plt.legend()
    output_path = output_dir / "andamento_ricerca_outfit.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    return output_path


def build_image_path_map(classified_csv_path):
    df = pd.read_csv(classified_csv_path)
    image_map = {}

    for _, row in df.iterrows():
        filename = str(row.get("filename", "")).strip()
        if not filename:
            continue

        candidates = []
        armadio_name = str(row.get("armadio", "")).strip()
        if armadio_name and armadio_name.lower() != "nan":
            candidates.append(Path("armadio") / armadio_name / filename)

        candidates.append(classified_csv_path.parent / filename)

        found = None
        for candidate in candidates:
            if candidate.exists():
                found = candidate
                break

        if found is None:
            basename = Path(filename).name
            for candidate in Path("armadio").rglob(basename):
                found = candidate
                break

        if found is not None:
            image_map[filename] = found

    return image_map

 # crea un collage finale con i capi dei migliori outfit sia nle caso dei vetsiti 
 # sia per la combo maglietta+pantalone
def create_top3_collage(rows, classified_csv_path, output_dir):
    image_map = build_image_path_map(classified_csv_path)
    columns = [
        ("giubbino_file", "giubbino_label", "Giubbino"),
        ("upper_file", "upper_label", "Upper"),
        ("pantalone_file", "pantalone_label", "Pantalone"),
        ("scarpe_file", "scarpe_label", "Scarpe"),
    ]

    n_rows = max(1, len(rows))
    fig, axes = plt.subplots(n_rows, 4, figsize=(20, 5.5 * n_rows))
    if n_rows == 1:
        axes = [axes]
    fig.suptitle("Top outfit trovati (3 vestito + 3 maglietta/pantalone)", fontsize=24, fontweight="bold")

    for row_idx, row in enumerate(rows):
        for col_idx, (file_key, label_key, header) in enumerate(columns):
            ax = axes[row_idx][col_idx]
            item_file = row[file_key]
            item_label = row[label_key]

            if item_file == "NO_GIUBBINO":
                ax.text(0.5, 0.5, "NO GIUBBINO", ha="center", va="center", fontsize=11)
                title = ax.set_title(f"{header}\n{item_label}", fontsize=17, fontweight="bold", pad=16, color="black")
                title.set_path_effects([pe.withStroke(linewidth=3.5, foreground="white")])
                ax.axis("off")
                continue

            if item_file == "NO_PANTALONE":
                ax.text(0.5, 0.5, "NO PANTALONE", ha="center", va="center", fontsize=11)
                title = ax.set_title(f"{header}\n{item_label}", fontsize=17, fontweight="bold", pad=16, color="black")
                title.set_path_effects([pe.withStroke(linewidth=3.5, foreground="white")])
                ax.axis("off")
                continue

            img_path = image_map.get(item_file)
            if img_path is not None and img_path.exists():
                with Image.open(img_path) as img:
                    ax.imshow(img.convert("RGB"), interpolation="lanczos")
            else:
                ax.text(0.5, 0.5, "Immagine non trovata", ha="center", va="center", fontsize=10)

            title = ax.set_title(f"{header}\n{item_label}", fontsize=17, fontweight="bold", pad=16, color="black")
            title.set_path_effects([pe.withStroke(linewidth=3.5, foreground="white")])
            ax.axis("off")

        axes[row_idx][0].text(
            -0.45,
            0.5,
            f"{row['gruppo']} #{row['rank_nel_gruppo']}\nScore: {row['score']}",
            transform=axes[row_idx][0].transAxes,
            fontsize=12,
            fontweight="bold",
            va="center",
            ha="left",
        )

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    collage_path = output_dir / "collage_top_3_outfit.png"
    plt.savefig(collage_path, dpi=360, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return collage_path

 # funzione principale che esegue l'algoritmo, seleziona gli outfit migliori e salva tutti gli output su file.
def run_evolution(classified_csv_path, meteo, stagione, stile, output_dir=OUTPUT_DIR):
    score_df = load_score_table()
    wardrobe = load_classified_wardrobe(classified_csv_path)

    meteo = normalize_text(meteo)
    stagione = normalize_text(stagione)
    stile = normalize_text(stile)

    if meteo not in METEO_OPTIONS:
        raise ValueError(f"Meteo non valido: {meteo}")
    if stagione not in STAGIONE_OPTIONS:
        raise ValueError(f"Stagione non valida: {stagione}")
    if stile not in STILE_OPTIONS:
        raise ValueError(f"Stile non valido: {stile}")

    check_feasibility(wardrobe, stagione, stile)

    random.seed(42)

    if not hasattr(creator, "FitnessMax"):
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    if not hasattr(creator, "Individual"):
        creator.create("Individual", list, fitness=creator.FitnessMax)

    max_upper_len = max(len(wardrobe["magliette"]), len(wardrobe["vestiti"]))
    max_giubbini = max(1, len(wardrobe["giubbini"]))

    low = [0, -1, 0, 0, 0]
    pants_up = max(0, len(wardrobe["pantaloni"]) - 1)
    up = [
        1,
        max_giubbini - 1,
        max_upper_len - 1,
        pants_up,
        len(wardrobe["scarpe"]) - 1,
    ]
# qui viene definito il toolbox per l'algpritmo, esso contiene le funzioni per
# generare individui, valutare la loro fitness, eseguire crossover e mutazione 
# e selezionare i migliori individui per la generazione successiva.
    toolbox = base.Toolbox()

    def init_individual():
        genes = [
            random.randint(low[0], up[0]),
            random.randint(low[1], up[1]),
            random.randint(low[2], up[2]),
            random.randint(low[3], up[3]),
            random.randint(low[4], up[4]),
        ]
        return creator.Individual(genes)

    def build_random_individual_for_group(group_name):
        genes = [
            random.randint(low[0], up[0]),
            random.randint(low[1], up[1]),
            random.randint(low[2], up[2]),
            random.randint(low[3], up[3]),
            random.randint(low[4], up[4]),
        ]
        if group_name == "vestito":
            genes[0] = 1
        elif group_name == "maglietta+pantalone":
            genes[0] = 0
        return creator.Individual(genes)

    def repair(ind):
        if stile == "sportivo":
            ind[0] = 0

        if len(wardrobe["vestiti"]) == 0:
            ind[0] = 0
        if len(wardrobe["magliette"]) == 0 and len(wardrobe["vestiti"]) > 0 and stile != "sportivo":
            ind[0] = 1
        if len(wardrobe["pantaloni"]) == 0 and len(wardrobe["vestiti"]) > 0:
            ind[0] = 1

        if stagione == "estate":
            ind[1] = -1
        else:
            if ind[1] < 0:
                ind[1] = 0

        for i in range(5):
            if ind[i] < low[i]:
                ind[i] = low[i]
            if ind[i] > up[i]:
                ind[i] = up[i]

        return ind

    def evaluate(ind):
        ind = repair(ind)

        decoded = decode_individual(ind, wardrobe, stagione, stile)
        score = 0.0

        if decoded["giubbino"] is not None:
            score += item_score(score_df, decoded["giubbino"].label, meteo, stagione, stile)

        score += item_score(score_df, decoded["upper"].label, meteo, stagione, stile)
        if decoded["pantalone"] is not None:
            score += item_score(score_df, decoded["pantalone"].label, meteo, stagione, stile)
        score += item_score(score_df, decoded["scarpa"].label, meteo, stagione, stile)

        return (score,)

    toolbox.register("individual", init_individual)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", evaluate)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", tools.mutUniformInt, low=low, up=up, indpb=0.25)
    toolbox.register("select", tools.selTournament, tournsize=3)

    pop_size = 120
    ngen = 60
    cxpb = 0.7
    mutpb = 0.3

    population = toolbox.population(n=pop_size)
    hof = tools.HallOfFame(maxsize=50)

    invalid = [ind for ind in population if not ind.fitness.valid]
    for ind, fit in zip(invalid, map(toolbox.evaluate, invalid)):
        ind.fitness.values = fit

    history_max = []
    history_avg = []

    for gen in range(1, ngen + 1):
        offspring = toolbox.select(population, len(population))
        offspring = list(map(toolbox.clone, offspring))

        for c1, c2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < cxpb:
                toolbox.mate(c1, c2)
                del c1.fitness.values
                del c2.fitness.values

        for mut in offspring:
            if random.random() < mutpb:
                toolbox.mutate(mut)
                del mut.fitness.values

        for ind in offspring:
            repair(ind)

        invalid = [ind for ind in offspring if not ind.fitness.valid]
        for ind, fit in zip(invalid, map(toolbox.evaluate, invalid)):
            ind.fitness.values = fit

        population[:] = offspring
        hof.update(population)

        fits = [ind.fitness.values[0] for ind in population]
        history_max.append(max(fits))
        history_avg.append(sum(fits) / len(fits))

        print_progress_bar(gen, ngen)

    print()

    unique_top = []
    seen = set()
    for ind in hof:
        decoded = decode_individual(ind, wardrobe, stagione, stile)
        signature = individual_signature(decoded)
        if signature in seen:
            continue
        seen.add(signature)
        unique_top.append((decoded, ind.fitness.values[0]))
        if len(unique_top) == 120:
            break

    top_vestito = []
    top_combo = []
    for decoded, score in unique_top:
        if decoded["tipo_outfit"] == "vestito" and len(top_vestito) < 3:
            top_vestito.append((decoded, score))
        elif decoded["tipo_outfit"] == "maglietta" and len(top_combo) < 3:
            top_combo.append((decoded, score))

        if len(top_vestito) == 3 and len(top_combo) == 3:
            break

    def complete_group_if_needed(group_name, selected_list, target_size=3, n_samples=6000):
        if len(selected_list) >= target_size:
            return selected_list

        chosen_signatures = {individual_signature(decoded) for decoded, _ in selected_list}
        pool = []

        for _ in range(n_samples):
            candidate = build_random_individual_for_group(group_name)
            repair(candidate)
            score = evaluate(candidate)[0]
            decoded = decode_individual(candidate, wardrobe, stagione, stile)

            if group_name == "vestito" and decoded["tipo_outfit"] != "vestito":
                continue
            if group_name == "maglietta+pantalone" and decoded["tipo_outfit"] != "maglietta":
                continue

            signature = individual_signature(decoded)
            if signature in chosen_signatures:
                continue

            pool.append((decoded, score))

        pool.sort(key=lambda x: x[1], reverse=True)
        for decoded, score in pool:
            signature = individual_signature(decoded)
            if signature in chosen_signatures:
                continue
            selected_list.append((decoded, score))
            chosen_signatures.add(signature)
            if len(selected_list) >= target_size:
                break

        return selected_list

    top_vestito = complete_group_if_needed("vestito", top_vestito)
    top_combo = complete_group_if_needed("maglietta+pantalone", top_combo)

    output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for rank, (decoded, score) in enumerate(top_vestito, start=1):
        giubbino_file = "NO_GIUBBINO"
        giubbino_label = "NO_GIUBBINO"
        pantalone_file = "NO_PANTALONE"
        pantalone_label = "NO_PANTALONE"
        if decoded["giubbino"] is not None:
            giubbino_file = decoded["giubbino"].filename
            giubbino_label = decoded["giubbino"].label
        if decoded["pantalone"] is not None:
            pantalone_file = decoded["pantalone"].filename
            pantalone_label = decoded["pantalone"].label

        rows.append(
            {
                "rank": len(rows) + 1,
                "rank_nel_gruppo": rank,
                "gruppo": "vestito",
                "score": round(score, 3),
                "meteo": meteo,
                "stagione": stagione,
                "stile": stile,
                "tipo_outfit": decoded["tipo_outfit"],
                "giubbino_file": giubbino_file,
                "giubbino_label": giubbino_label,
                "upper_file": decoded["upper"].filename,
                "upper_label": decoded["upper"].label,
                "pantalone_file": pantalone_file,
                "pantalone_label": pantalone_label,
                "scarpe_file": decoded["scarpa"].filename,
                "scarpe_label": decoded["scarpa"].label,
            }
        )

    for rank, (decoded, score) in enumerate(top_combo, start=1):
        giubbino_file = "NO_GIUBBINO"
        giubbino_label = "NO_GIUBBINO"
        pantalone_file = "NO_PANTALONE"
        pantalone_label = "NO_PANTALONE"
        if decoded["giubbino"] is not None:
            giubbino_file = decoded["giubbino"].filename
            giubbino_label = decoded["giubbino"].label
        if decoded["pantalone"] is not None:
            pantalone_file = decoded["pantalone"].filename
            pantalone_label = decoded["pantalone"].label

        rows.append(
            {
                "rank": len(rows) + 1,
                "rank_nel_gruppo": rank,
                "gruppo": "maglietta+pantalone",
                "score": round(score, 3),
                "meteo": meteo,
                "stagione": stagione,
                "stile": stile,
                "tipo_outfit": decoded["tipo_outfit"],
                "giubbino_file": giubbino_file,
                "giubbino_label": giubbino_label,
                "upper_file": decoded["upper"].filename,
                "upper_label": decoded["upper"].label,
                "pantalone_file": pantalone_file,
                "pantalone_label": pantalone_label,
                "scarpe_file": decoded["scarpa"].filename,
                "scarpe_label": decoded["scarpa"].label,
            }
        )

    results_df = pd.DataFrame(rows)
    csv_out = output_dir / "top_3_outfit.csv"
    history_csv_out = output_dir / "storico_fitness.csv"
    txt_out = output_dir / "top_3_outfit.txt"
    graph_out = plot_evolution(history_max, history_avg, output_dir)
    collage_out = create_top3_collage(rows, classified_csv_path, output_dir)

    results_df.to_csv(csv_out, index=False)
    pd.DataFrame(
        {
            "generazione": list(range(1, len(history_max) + 1)),
            "best_fitness": history_max,
            "avg_fitness": history_avg,
        }
    ).to_csv(history_csv_out, index=False)

    with txt_out.open("w", encoding="utf-8") as f:
        f.write("Top outfit separati per tipo\n")
        f.write(f"Meteo: {meteo} | Stagione: {stagione} | Stile: {stile}\n\n")
        f.write("Top 3 vestito:\n")
        for row in [r for r in rows if r["gruppo"] == "vestito"]:
            f.write(f"#{row['rank_nel_gruppo']} - score={row['score']} ({row['tipo_outfit']})\n")
            f.write(f"  giubbino: {row['giubbino_file']} [{row['giubbino_label']}]\n")
            f.write(f"  upper: {row['upper_file']} [{row['upper_label']}]\n")
            f.write(f"  pantalone: {row['pantalone_file']} [{row['pantalone_label']}]\n")
            f.write(f"  scarpe: {row['scarpe_file']} [{row['scarpe_label']}]\n\n")

        f.write("Top 3 maglietta+pantalone:\n")
        for row in [r for r in rows if r["gruppo"] == "maglietta+pantalone"]:
            f.write(f"#{row['rank_nel_gruppo']} - score={row['score']} ({row['tipo_outfit']})\n")
            f.write(f"  giubbino: {row['giubbino_file']} [{row['giubbino_label']}]\n")
            f.write(f"  upper: {row['upper_file']} [{row['upper_label']}]\n")
            f.write(f"  pantalone: {row['pantalone_file']} [{row['pantalone_label']}]\n")
            f.write(f"  scarpe: {row['scarpe_file']} [{row['scarpe_label']}]\n\n")

    return rows, csv_out, history_csv_out, txt_out, graph_out, collage_out


def main():
    print("=== Creiamo il tuo outfit ===")
    classified_path = choose_classified_file()
    output_dir = build_output_dir_for_classified(classified_path)

    meteo = ask_choice("Seleziona meteo:", METEO_OPTIONS)
    stagione = ask_choice("Seleziona stagione:", STAGIONE_OPTIONS)
    stile = ask_choice("Seleziona stile:", STILE_OPTIONS)

    rows, csv_out, history_csv_out, txt_out, graph_out, collage_out = run_evolution(
        classified_csv_path=classified_path,
        meteo=meteo,
        stagione=stagione,
        stile=stile,
        output_dir=output_dir,
    )

    print("\nTop 3 outfit con vestito:")
    for row in [r for r in rows if r["gruppo"] == "vestito"]:
        if row["pantalone_label"] == "NO_PANTALONE":
            combo = f"{row['upper_label']} + {row['scarpe_label']}"
        else:
            combo = f"{row['upper_label']} + {row['pantalone_label']} + {row['scarpe_label']}"

        print(f"#{row['rank_nel_gruppo']} score={row['score']} | {row['tipo_outfit']} | {combo}")

    print("\nTop 3 outfit con maglietta+pantalone:")
    for row in [r for r in rows if r["gruppo"] == "maglietta+pantalone"]:
        if row["pantalone_label"] == "NO_PANTALONE":
            combo = f"{row['upper_label']} + {row['scarpe_label']}"
        else:
            combo = f"{row['upper_label']} + {row['pantalone_label']} + {row['scarpe_label']}"

        print(f"#{row['rank_nel_gruppo']} score={row['score']} | {row['tipo_outfit']} | {combo}")

    print(f"\nOutput salvati in: {output_dir}")
    print(f"- CSV top 3: {csv_out}")
    print(f"- CSV storico fitness: {history_csv_out}")
    print(f"- TXT: {txt_out}")
    print(f"- Grafico: {graph_out}")
    print(f"- Collage: {collage_out}")


if __name__ == "__main__":
    main()
