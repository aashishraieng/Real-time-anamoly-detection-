from flask import Flask, render_template_string
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
import time

app = Flask(__name__)

# -------- LOAD & PROCESS DATA (ONLY ONCE) --------
df = pd.read_csv("data/traffic.csv")
df.columns = df.columns.str.strip()

labels = df["Label"]
y_true = labels.apply(lambda x: 0 if x == "BENIGN" else 1)

df = df.drop(columns=["Label"])

# clean
df.replace([np.inf, -np.inf], np.nan, inplace=True)
df = df.dropna()
y_true = y_true[df.index]

# feature selection
df = df.loc[:, df.nunique() > 1]

corr = df.corr().abs()
upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
to_drop = [col for col in upper.columns if any(upper[col] > 0.9)]
df = df.drop(columns=to_drop)

# split
X_train = df[y_true == 0]

# scale
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)

# model
model = IsolationForest(n_estimators=100, contamination=0.2, random_state=42)
model.fit(X_train)

# -------- DASHBOARD ROUTE (DYNAMIC) --------
@app.route("/")
def home():

    # 🔥 simulate live traffic (new sample every request)
    sample_df = df.sample(200)

    X_sample = scaler.transform(sample_df)
    pred_sample = model.predict(X_sample)
    y_sample = np.where(pred_sample == 1, 0, 1)

    total = len(y_sample)
    anomalies = int(np.sum(y_sample == 1))
    normal = int(np.sum(y_sample == 0))

    anomaly_df = sample_df[y_sample == 1].head(10)

    return render_template_string("""
    <html>
    <head>
        <title>Network Anomaly Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

        <style>
            body {
                font-family: Arial;
                text-align: center;
            }
            table {
                margin: auto;
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid black;
                padding: 5px;
                font-size: 12px;
            }
        </style>
    </head>

    <body>

        <h1>Network Anomaly Detection Dashboard (Live Simulation)</h1>

        <h2>Total Traffic: {{total}}</h2>
        <h2>Normal: {{normal}}</h2>
        <h2>Anomalies: {{anomalies}}</h2>

        <canvas id="chart" width="400" height="200"></canvas>

        <script>
            const ctx = document.getElementById('chart');

            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Normal', 'Anomalies'],
                    datasets: [{
                        label: 'Traffic Distribution',
                        data: [{{normal}}, {{anomalies}}],
                    }]
                }
            });
        </script>

        <h2>Live Detected Anomalies</h2>

        <table>
            <tr>
                {% for col in columns %}
                    <th>{{col}}</th>
                {% endfor %}
            </tr>

            {% for row in rows %}
            <tr>
                {% for val in row %}
                    <td>{{val}}</td>
                {% endfor %}
            </tr>
            {% endfor %}
        </table>

    </body>
    </html>
    """,
    total=total,
    normal=normal,
    anomalies=anomalies,
    columns=anomaly_df.columns,
    rows=anomaly_df.values.tolist()
    )

# -------- RUN --------
if __name__ == "__main__":
    app.run(debug=True)