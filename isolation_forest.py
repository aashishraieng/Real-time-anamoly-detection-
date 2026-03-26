# isolation_forest.py

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report

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

# MODEL
model = IsolationForest(n_estimators=100, contamination=0.2, random_state=42)
model.fit(X_train)

pred = model.predict(X_test)
y_pred = np.where(pred == 1, 0, 1)

print("=== Isolation Forest ===")
print(classification_report(y_test, y_pred))