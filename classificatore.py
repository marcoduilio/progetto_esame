import os
import time
import zipfile
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from PIL import Image

#in questa porzione del codice viene definito il dataset utilizzando i file importati da noi
DATA_DIR = Path("dataset")
ZIP_PATH = DATA_DIR / "abiti.zip"
LABELS_PATH = DATA_DIR / "labels_corretti.csv"
ARMADIO_DIR = Path("armadio")


def select_armadio_folder(base_dir=ARMADIO_DIR):
    if not base_dir.exists():
        raise FileNotFoundError(f"Cartella non trovata: {base_dir}")

    subfolders = sorted([p for p in base_dir.iterdir() if p.is_dir()], key=lambda p: p.name.lower())

    if not subfolders:
        print(f"Nessuna sottocartella trovata in {base_dir}. Uso la cartella principale.")
        return base_dir

    print("Seleziona l'armadio da classificare:")
    for idx, folder in enumerate(subfolders, start=1):
        print(f"{idx}. {folder.name}")

    while True:
        choice = input("Inserisci il numero dell'armadio: ").strip()
        if not choice.isdigit():
            print("Scelta non valida. Inserisci un numero.")
            continue

        selected_index = int(choice)
        if 1 <= selected_index <= len(subfolders):
            selected_folder = subfolders[selected_index - 1]
            print(f"Armadio selezionato: {selected_folder.name}")
            return selected_folder

        print(f"Scelta non valida. Inserisci un numero tra 1 e {len(subfolders)}.")

# in questa porzione del codice viene definita la funzione per risolvere il percorso del file delle etichette, restituendo il percorso corretto se esiste, altrimenti sollevando un'eccezione.
def resolve_labels_path():
    if LABELS_PATH.exists():
        return LABELS_PATH

    fallback = LABELS_PATH.with_suffix(".csv")
    if fallback.exists():
        return fallback

    raise FileNotFoundError(
        f"File etichette non trovato: {LABELS_PATH} o {fallback}"
    )

#in questa porzione del codice viene definito un dizionario che mappa le classi di abbigliamento in macro-categorie.

MACRO_CATEGORY_MAP = {
    "Giubbini": {
        "blazer",
        "giacca in pelle",
        "giacchetta",
        "giubbino invernale",
        "giubbino leggero",
        "montgomery",
    },
    "magliette": {
        "body",
        "camicia a maniche corte",
        "camicia a maniche lunghe",
        "dolce vita",
        "felpa",
        "maglietta a maniche corte",
        "maglietta a maniche lunghe",
        "pullover",
        "tank top",
        "top",
    },
    "pantaloni": {
        "jeans",
        "pantaloncino",
        "pantalone da ginnastica",
        "pantalone formale",
        "salopette corta",
        "salopette lunga",
    },
    "vestiti": {
        "mini vestito",
        "mini vestito a bretelle",
        "mini vestito a maniche lunghe",
        "vestito da sera",
        "vestito da sera a maniche lunghe",
        "vestito intero",
        "vestito intero a bretelle",
        "vestito intero a maniche lunghe",
    },
    "scarpe": {
        "ciabatte",
        "sandali classici",
        "sandali con tacco",
        "scarpe da ginnastica",
        "stivaletti",
        "stivali",
        "stivali con tacco",
        "stivali invernali",
    },
}

#in questa porzione vengono estratte le caratteristiche delle immagini.
def extract_image_features(img):
    img = img.convert("L")
    img = img.resize((44, 44))
    arr = np.asarray(img, dtype=np.float32) / 255.0

    resized = np.array(Image.fromarray(np.uint8(arr * 255.0)).resize((32, 32)))
    resized = resized.astype(np.float32) / 255.0

    pooled = np.mean(resized, axis=(0, 1))
    std = np.std(resized, axis=(0, 1))
    flat = resized.reshape(-1)

    gradients = np.abs(np.diff(resized, axis=0)).mean() + np.abs(np.diff(resized, axis=1)).mean()
    edges = np.gradient(resized)
    edge_strength = np.sqrt(edges[0] ** 2 + edges[1] ** 2).mean()

    hist = np.histogram(arr, bins=16, range=(0, 1))[0]

    features = np.concatenate([flat, [pooled, std, gradients, edge_strength], hist])
    return features.astype(np.float32)

# in questa porzione vengono caricate le caratteristiche delle immagini da una cartella specificata, restituendo le caratteristiche e i nomi dei file.
def load_training_features():
    labels_df = pd.read_csv(resolve_labels_path())
    with zipfile.ZipFile(ZIP_PATH) as zf:
        images = []
        names = []
        labels = []
        for filename, label in zip(labels_df["filename"], labels_df["sub_class"]):
            with zf.open(filename) as f:
                img = Image.open(f).convert("RGB")
                img = img.resize((44, 44))
                arr = np.asarray(img, dtype=np.float32) / 255.0
                images.append(arr.transpose(2, 0, 1))
                names.append(filename)
                labels.append(label)

    X = np.stack(images)
    return X, np.array(labels), np.array(names)

# 
def load_folder_features(folder):
    if not folder.exists():
        return [], []

    image_files = []
    for ext in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
        image_files.extend(folder.rglob(f"*{ext}"))

    features = []
    names = []
    for path in image_files:
        img = Image.open(path).convert("RGB")
        img = img.resize((44, 44))
        arr = np.asarray(img, dtype=np.float32) / 255.0
        features.append(arr.transpose(2, 0, 1))
        names.append(str(path.relative_to(folder)).replace(os.sep, '/'))

    if not features:
        return [], []

    return np.stack(features), names

#qui viene definita la rete neurale convoluzionale per la classificazione degli abiti, con due strati convoluzionali, due strati di pooling, uno strato completamente connesso e uno strato di dropout per prevenire l'overfitting.
class ClothingCNN(nn.Module):
    def __init__(self, num_classes=38):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.relu1 = nn.ReLU()
        self.pool1 = nn.MaxPool2d(kernel_size=2)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.relu2 = nn.ReLU()
        self.pool2 = nn.MaxPool2d(kernel_size=2)
        self.flatten = nn.Flatten()
        self.fc1 = nn.Linear(64 * 11 * 11, 256)
        self.relu3 = nn.ReLU()
        self.dropout = nn.Dropout(p=0.25)
        self.fc2 = nn.Linear(256, num_classes)

    def forward(self, x):
        x = self.pool1(self.relu1(self.conv1(x)))
        x = self.pool2(self.relu2(self.conv2(x)))
        x = self.flatten(x)
        x = self.dropout(self.relu3(self.fc1(x)))
        return self.fc2(x)

#qui vengono specificate le cassi di abbigliamento che il modello può classificare, con un dizionario che associa ogni classe a un indice numerico.
def build_supervised_model(output_dir="risultati", armadio_name="armadio"):
    X, y, _ = load_training_features()

    class_to_idx = {cls: idx for idx, cls in enumerate(sorted(set(y)))}
    y_idx = np.array([class_to_idx[label] for label in y])

    X_tensor = torch.tensor(X, dtype=torch.float32)
    y_tensor = torch.tensor(y_idx, dtype=torch.long)

    indices = np.arange(len(X_tensor))
    rng = np.random.default_rng(42)
    rng.shuffle(indices)

    split = int(0.9 * len(indices))
    train_idx = indices[:split]
    val_idx = indices[split:]

    train_x = X_tensor[train_idx]
    train_y = y_tensor[train_idx]
    val_x = X_tensor[val_idx]
    val_y = y_tensor[val_idx]

    train_dataset = torch.utils.data.TensorDataset(train_x, train_y)
    val_dataset = torch.utils.data.TensorDataset(val_x, val_y)
    class_counts = torch.bincount(train_y)
    class_weights = 1.0 / torch.pow(class_counts.float().clamp(min=1), 0.586)
    class_weights = class_weights / class_weights.mean()

    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=128, shuffle=True, num_workers=0)
    val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=128, shuffle=False, num_workers=0)

    model = ClothingCNN(num_classes=len(class_to_idx)).to("cpu")
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.00072, weight_decay=1e-4)

    num_epochs = 10
    history = []
    best_val_loss = float("inf")
    best_state = None
    patience = 3
    epochs_without_improve = 0

    total_batches = len(train_loader) * num_epochs
    start_time = time.time()
    print(f"Training previsto: circa {total_batches} batch da elaborare. Il modello potrebbe impiegare qualche minuto.")

    batch_times = []
    for epoch in range(1, num_epochs + 1):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for batch_idx, (xb, yb) in enumerate(train_loader, 1):
            batch_start = time.time()
            optimizer.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            optimizer.step()
            batch_times.append(time.time() - batch_start)

            running_loss += loss.item() * yb.size(0)
            preds = logits.argmax(dim=1)
            correct += (preds == yb).sum().item()
            total += yb.size(0)

            if batch_idx % max(1, len(train_loader) // 4) == 0 or batch_idx == len(train_loader):
                progress = batch_idx / len(train_loader)
                bar_width = 30
                filled = int(progress * bar_width)
                bar = "#" * filled + "-" * (bar_width - filled)
                print(f"\rTraining: [{bar}] {batch_idx}/{len(train_loader)} batches", end="", flush=True)

        if len(batch_times) >= 1:
            avg_batch_time = np.mean(batch_times)
            estimated_total_time = avg_batch_time * total_batches
            print(f"Stima tempo totale: {estimated_total_time:.1f} secondi ({estimated_total_time / 60:.1f} minuti)")

        train_loss = running_loss / total
        train_acc = correct / total

        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for xb, yb in val_loader:
                logits = model(xb)
                loss = criterion(logits, yb)
                val_loss += loss.item() * yb.size(0)
                val_correct += (logits.argmax(dim=1) == yb).sum().item()
                val_total += yb.size(0)

        val_loss /= val_total
        val_acc = val_correct / val_total
        history.append((epoch, train_loss, train_acc, val_loss, val_acc))
        print(f"\nEpoch {epoch}/{num_epochs} - train_loss: {train_loss:.4f} - train_acc: {train_acc:.4f} - val_loss: {val_loss:.4f} - val_acc: {val_acc:.4f}")

        if val_loss < best_val_loss - 1e-4:
            best_val_loss = val_loss
            best_state = {k: v.clone().detach() for k, v in model.state_dict().items()}
            epochs_without_improve = 0
        else:
            epochs_without_improve += 1
            if epochs_without_improve >= patience:
                print("Early stopping triggered.")
                break

    if best_state is not None:
        model.load_state_dict(best_state)

    elapsed = time.time() - start_time
    print(f"Tempo totale stimato/effettivo: {elapsed:.1f} secondi")

    plot_training_history(history, output_dir=output_dir, armadio_name=armadio_name)

    return model, class_to_idx, history


def get_macro_category(label):
    for macro_category, classes in MACRO_CATEGORY_MAP.items():
        if label in classes:
            return macro_category
    return "non assegnata"


#salva le predizioni in un file csv, con quattro colonne: armadio, nome del file, etichetta predetta e macroetichetta.
def save_predictions_csv(results, armadio_name, output_dir="risultati"):
    output_path = Path(output_dir) / f"{armadio_name} classificato.csv"
    output_path.parent.mkdir(exist_ok=True)

    df = pd.DataFrame(results, columns=["armadio", "filename", "label", "macroetichetta"])
    df.to_csv(output_path, index=False)
    print(f"File CSV salvato in: {output_path}")
    return output_path

# crea un'immagine con i vestiti dell'armadio e le rispettive etichette e macroetichette.
def classify_armadio(output_dir="risultati", armadio_path=ARMADIO_DIR):
    armadio_name = armadio_path.name
    model, class_to_idx, history = build_supervised_model(output_dir=output_dir, armadio_name=armadio_name)
    X_test, names = load_folder_features(armadio_path)

    if len(X_test) == 0:
        print("Nessuna immagine trovata nella cartella armadio")
        return []

    X_tensor = torch.tensor(X_test, dtype=torch.float32)
    with torch.no_grad():
        logits = model(X_tensor)
        pred_indices = torch.argmax(logits, dim=1).tolist()

    idx_to_class = {idx: cls for cls, idx in class_to_idx.items()}
    predicted_labels = [idx_to_class[idx] for idx in pred_indices]

    results = []
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    display_items = []

    for image_name, label in zip(names, predicted_labels):
        macro_label = get_macro_category(label)
        results.append((armadio_name, image_name, label, macro_label))

        image_path = armadio_path / image_name
        if image_path.exists():
            img = Image.open(image_path).convert("RGB")
            display_items.append((img, label, macro_label))

    save_predictions_csv(results, armadio_name=armadio_name, output_dir=output_dir)

    if display_items:
        grouped_items = {macro_label: [] for macro_label in MACRO_CATEGORY_MAP}
        grouped_items["non assegnata"] = []

        for img, label, macro_label in display_items:
            grouped_items.setdefault(macro_label, []).append((img, label))

        grouped_items = {macro_label: items for macro_label, items in grouped_items.items() if items}

        cols = 5
        layout_rows = []
        for macro_label, items in grouped_items.items():
            layout_rows.append(("title", macro_label))
            for start_idx in range(0, len(items), cols):
                layout_rows.append(("images", items[start_idx:start_idx + cols]))

        height_ratios = [0.18 if row_type == "title" else 1.0 for row_type, _ in layout_rows]
        figure_height = sum(1.2 if row_type == "title" else 5.6 for row_type, _ in layout_rows)

        fig = plt.figure(figsize=(5.8 * cols, figure_height))
        grid = fig.add_gridspec(len(layout_rows), cols, height_ratios=height_ratios)

        for row_idx, (row_type, row_data) in enumerate(layout_rows):
            if row_type == "title":
                title_ax = fig.add_subplot(grid[row_idx, :])
                title_ax.axis("off")
                title_ax.text(
                    0.5,
                    0.5,
                    row_data,
                    ha="center",
                    va="center",
                    fontsize=24,
                    fontweight="bold",
                    color="black",
                )
                continue

            for col_idx in range(cols):
                ax = fig.add_subplot(grid[row_idx, col_idx])
                if col_idx < len(row_data):
                    img, label = row_data[col_idx]
                    ax.imshow(img)
                    title = ax.set_title(
                        label,
                        fontsize=18,
                        fontweight="bold",
                        pad=14,
                        color="black",
                    )
                    title.set_path_effects([pe.withStroke(linewidth=2.0, foreground="white")])
                ax.axis("off")

        fig.subplots_adjust(wspace=0.30, hspace=0.42, top=0.98, bottom=0.03)
        output_file = output_path / f"foto vestiti {armadio_name} classificati.png"
        plt.savefig(output_file, dpi=320, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(f"Immagine finale salvata in: {output_file}")

    return results

# in questa porzione di codice viene definita la funzione per plottare la storia dell'addestramento, mostrando l'andamento della loss e dell'accuracy sia per il training che per la validazione.

def plot_training_history(history, output_dir="risultati", armadio_name="armadio"):
    if not history:
        return

    epochs = [entry[0] for entry in history]
    train_losses = [entry[1] for entry in history]
    train_accs = [entry[2] for entry in history]
    val_losses = [entry[3] for entry in history]
    val_accs = [entry[4] for entry in history]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].plot(epochs, train_losses, "-o", label="Train loss")
    axes[0].plot(epochs, val_losses, "--o", label="Validation loss")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(epochs, train_accs, "-o", label="Train accuracy")
    axes[1].plot(epochs, val_accs, "--o", label="Validation accuracy")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Accuracy")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    output_path = Path(output_dir) / f"training history {armadio_name} classificato.png"
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Grafico salvato in: {output_path}")


if __name__ == "__main__":
    selected_armadio = select_armadio_folder()
    output_dir = f"risultati {selected_armadio.name}"
    results = classify_armadio(output_dir=output_dir, armadio_path=selected_armadio)
    for armadio_name, name, label, macro_label in results:
        print(f"[{armadio_name}] {name}: {label} ({macro_label})")
