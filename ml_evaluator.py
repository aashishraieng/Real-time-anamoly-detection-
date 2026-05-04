import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import torch
import torch.nn as nn
import os

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

class MLEvaluator:
    def __init__(self):
        self.csv_path = "data/traffic.csv"
        self.cache = {}

    def _load_data(self):
        if not os.path.exists(self.csv_path):
            return None, None, None, None

        df = pd.read_csv(self.csv_path)
        df.columns = df.columns.str.strip()

        if "Label" not in df.columns:
            return None, None, None, None

        labels = df["Label"]
        y_true = labels.apply(lambda x: 0 if x == "BENIGN" else 1)

        df = df.drop(columns=["Label"])
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.dropna()
        y_true = y_true[df.index]

        df = df.loc[:, df.nunique() > 1]
        corr = df.corr().abs()
        upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
        to_drop = [col for col in upper.columns if any(upper[col] > 0.9)]
        df = df.drop(columns=to_drop)

        X = df.values
        y = y_true.values

        # Simplistic split
        X_train = df[y_true == 0].values[:5000] # Use subset for speed
        X_test = X[:2000]
        y_test = y[:2000]

        scaler = StandardScaler()
        if len(X_train) == 0:
             X_train = X[:1000] # Fallback
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)

        return X_train, X_test, y_test, scaler

    def evaluate_model(self, model_name):
        if model_name in self.cache:
            return self.cache[model_name]

        X_train, X_test, y_test, _ = self._load_data()
        if X_train is None:
            return {"error": "Dataset not found or invalid format"}

        y_pred = None

        if model_name == "Isolation Forest":
            clf = IsolationForest(n_estimators=50, contamination=0.2, random_state=42)
            clf.fit(X_train)
            pred = clf.predict(X_test)
            y_pred = np.where(pred == 1, 0, 1)

        elif model_name == "LOF":
            clf = LocalOutlierFactor(n_neighbors=20, contamination=0.2, novelty=True)
            clf.fit(X_train)
            pred = clf.predict(X_test)
            y_pred = np.where(pred == 1, 0, 1)

        elif model_name == "Autoencoder":
            input_dim = X_train.shape[1]
            model = Autoencoder(input_dim)
            criterion = nn.MSELoss()
            optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

            X_train_t = torch.tensor(X_train, dtype=torch.float32)
            X_test_t = torch.tensor(X_test, dtype=torch.float32)

            for _ in range(5): # Very short train for demo
                output = model(X_train_t)
                loss = criterion(output, X_train_t)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            with torch.no_grad():
                recon = model(X_test_t)
                error = torch.mean((X_test_t - recon) ** 2, dim=1).numpy()
            
            threshold = np.percentile(error, 80)
            y_pred = (error > threshold).astype(int)

        elif model_name == "Hybrid (IF + AE)":
            # Quick combine
            clf = IsolationForest(n_estimators=50, contamination=0.2, random_state=42)
            clf.fit(X_train)
            if_pred = clf.predict(X_test)
            if_pred = np.where(if_pred == 1, 0, 1)

            input_dim = X_train.shape[1]
            model = Autoencoder(input_dim)
            criterion = nn.MSELoss()
            optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
            X_train_t = torch.tensor(X_train, dtype=torch.float32)
            X_test_t = torch.tensor(X_test, dtype=torch.float32)
            for _ in range(5):
                output = model(X_train_t)
                loss = criterion(output, X_train_t)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            with torch.no_grad():
                recon = model(X_test_t)
                error = torch.mean((X_test_t - recon) ** 2, dim=1).numpy()
            threshold = np.percentile(error, 80)
            ae_pred = (error > threshold).astype(int)

            y_pred = np.logical_or(if_pred, ae_pred).astype(int)

        else:
            return {"error": "Unknown model"}

        acc = accuracy_score(y_test, y_pred)
        # Handle cases where true positive is 0, setting zero_division=0
        precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary', zero_division=0)
        
        # In case our mock dataset piece doesn't have positive labels, calculate macro
        if np.sum(y_test) == 0:
            precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='macro', zero_division=0)

        result = {
            "accuracy": round(acc, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4)
        }
        self.cache[model_name] = result
        return result

    def offline_csv_eval(self, file_stream):
        # We process the uploaded CSV via Isolation Forest for a quick anomaly count
        try:
            df = pd.read_csv(file_stream)
            initial_count = len(df)
            
            # Simple clean just to pass to scaler
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
            df = df.dropna()
            
            # Use columns that have numeric data
            df_numeric = df.select_dtypes(include=[np.number])
            
            if df_numeric.empty:
                return {"error": "CSV requires numeric columns"}
            
            from sklearn.ensemble import IsolationForest
            clf = IsolationForest(n_estimators=50, contamination=0.1, random_state=42)
            preds = clf.fit_predict(df_numeric.values)
            
            anomalies_count = int(np.sum(preds == -1))
            normal_count = int(np.sum(preds == 1))
            
            return {
                "total_rows": initial_count,
                "processed_rows": len(df_numeric),
                "anomalies": anomalies_count,
                "normal": normal_count
            }
        except Exception as e:
            return {"error": str(e)}

evaluator = MLEvaluator()
