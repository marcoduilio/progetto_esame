from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np
from keras.datasets import fashion_mnist

# Carica il dataset Fashion-MNIST
(X_train_full, y_train_full), (X_test, y_test) = fashion_mnist.load_data()

# Normalizzazione dei pixel tra 0 e 1
X_train_full = X_train_full.astype('float32') / 255.0
X_test = X_test.astype('float32') / 255.0

# Appiattimento delle immagini 28x28 in vettori di 784 feature
X_train_full_flat = X_train_full.reshape(len(X_train_full), -1)
X_test_flat = X_test.reshape(len(X_test), -1)

# Divisione train/validation
X_train, X_val, y_train, y_val = train_test_split(
    X_train_full_flat,
    y_train_full,
    test_size=0.2,
    random_state=42,
    stratify=y_train_full
)

# Standardizzazione
scaler = StandardScaler()
X_train_std = scaler.fit_transform(X_train)
X_val_std = scaler.transform(X_val)
X_test_std = scaler.transform(X_test_flat)

# PCA a 2 componenti
pca = PCA(n_components=2, random_state=42)
X_train_pca = pca.fit_transform(X_train_std)
X_val_pca = pca.transform(X_val_std)
X_test_pca = pca.transform(X_test_std)

print('Class labels:', np.unique(y_train_full))
print('Explained variance ratio:', pca.explained_variance_ratio_)

# Esempio di risultato in DataFrame
result = pd.DataFrame({
    'principal_component': ['PC1', 'PC2'],
    'explained_variance_ratio': pca.explained_variance_ratio_
})
print(result)

class_names = ['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat', 'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot']

print('Dataset labels:', np.unique(y_train_full))
print('Dataset label names:', [class_names[label] for label in np.unique(y_train_full)])

df = pd.DataFrame(X_train_pca, columns=['PC1', 'PC2'])
df['label'] = y_train
df['label_name'] = [class_names[i] for i in y_train]
print(df.head())
