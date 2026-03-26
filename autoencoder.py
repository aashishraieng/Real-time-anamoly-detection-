# autoencoder.py

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import torch
import torch.nn as nn

# LOAD
df = pd.read_csv("data/traffic.csv")
df.columns = df.columns.str.strip()

labels = df["Label"]
y_true = labels.apply(lambda x: 0 if x == "BENIGN" else 1)

df = df.drop(columns=["Label"])

# CLEAN
df.replace([np.inf, -np.inf], np.nan, inplace=True)
df = df.dropna()
y_true = y_true[df.index]

# FEATURE SELECTION
df = df.loc[:, df.nunique() > 1]

corr = df.corr().abs()
upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
to_drop = [col for col in upper.columns if any(upper[col] > 0.9)]
df = df.drop(columns=to_drop)

# SPLIT
X_train = df[y_true == 0]
X_test = df
y_test = y_true

# SCALE
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

X_train = torch.tensor(X_train, dtype=torch.float32)
X_test = torch.tensor(X_test, dtype=torch.float32)

# MODEL
class Autoencoder(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 8)
        )
        self.decoder = nn.Sequential(
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, input_dim)
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))

model = Autoencoder(X_train.shape[1])

criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

# TRAIN
for epoch in range(10):
    output = model(X_train)
    loss = criterion(output, X_train)

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

# TEST
with torch.no_grad():
    recon = model(X_test)
    error = torch.mean((X_test - recon) ** 2, dim=1).numpy()

threshold = np.percentile(error, 60)
y_pred = (error > threshold).astype(int)

print("=== Autoencoder ===")
print(classification_report(y_test, y_pred))