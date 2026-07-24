import io
import pathlib
import zipfile
import pandas as pd
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
import torch

DATA_DIR = pathlib.Path("dataset")
ZIP_PATH = DATA_DIR / "abiti.zip"
LABELS_PATH = DATA_DIR / "labels_corretti.cvs"

# Leggi il CSV dei label
labels_df = pd.read_csv(LABELS_PATH)
print(labels_df.head())

# Linea che mostra quanti e quali label ci sono
print("Conteggio labels:")
print(labels_df["sub_class"].value_counts())

# Mappa i label in indici numerici
class_to_idx = {cls: i for i, cls in enumerate(sorted(labels_df["sub_class"].unique()))}
labels_df["label"] = labels_df["sub_class"].map(class_to_idx)

print("Classi disponibili:", class_to_idx)

class ZipImageDataset(Dataset):
    def __init__(self, zip_path, labels_csv, transform=None):
        self.zip_path = zip_path
        self.transform = transform
        self.labels_df = pd.read_csv(labels_csv)
        self.zip_file = zipfile.ZipFile(zip_path)

        # mappatura label -> id
        self.class_to_idx = {
            cls: i for i, cls in enumerate(sorted(self.labels_df["sub_class"].unique()))
        }
        self.labels_df["label"] = self.labels_df["sub_class"].map(self.class_to_idx)

        self.file_list = self.labels_df["filename"].tolist()
        self.targets = self.labels_df["label"].tolist()

    def __len__(self):
        return len(self.file_list)

    def __getitem__(self, idx):
        filename = self.file_list[idx]
        label = self.targets[idx]

        with self.zip_file.open(filename) as f:
            image = Image.open(f).convert("RGB")

        if self.transform is not None:
            image = self.transform(image)

        return image, label

# Trasformazioni facoltative
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

dataset = ZipImageDataset(ZIP_PATH, LABELS_PATH, transform=transform)

print("Dataset creato con", len(dataset), "immagini")

loader = DataLoader(dataset, batch_size=4, shuffle=True)

for images, labels in loader:
    print("Batch images:", images.shape)
    print("Batch labels:", labels)
    break