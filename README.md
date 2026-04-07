# Real-Time Network Anomaly Detection System

This repository contains a suite of tools and machine learning models for detecting anomalies in network traffic. It includes scripts for training different anomaly detection algorithms, as well as lightweight and dashboard-based applications to monitor live network traffic via packet sniffing.

## 📂 Project Structure and File Descriptions

### Web & CLI Applications
*   **`live_app.py`** 
    **Description:** This is the flagship real-time dashboard application. It uses `Flask` to host a web UI and `scapy` running on a background thread to continuously sniff live packets from your actual network interfaces. It calculates packet sizes, identifies protocols, tracks traffic rates per IP, and flags heuristic anomalies (e.g., floods, unusually large packets). The web dashboard updates automatically every 3 seconds to display the latest alerts.
*   **`app.py`**
    **Description:** A simulated version of the live dashboard. Unlike `live_app.py` which looks at actual network traffic, this script continuously samples data points from the offline dataset (`data/traffic.csv`). It processes them through a pre-trained `IsolationForest` model to detect statistical anomalies. This is excellent for testing the ML pipeline visually. 
*   **`sniffer.py`**
    **Description:** A lightweight, command-line interface (CLI) real-time packet sniffer. It intercepts live network traffic using `scapy` and outputs logs directly to the console. It includes basic rule-based checks (like packet size and transmission rate) to throw `🚨 ANOMALY` warnings instantly.

### Machine Learning Models
*   **`autoencoder.py`**
    **Description:** Implements a Neural Network Autoencoder using `PyTorch`. It trains exclusively on normal ("BENIGN") network traffic so it learns reconstruction. When it tries to reconstruct anomalous traffic, the error rate spikes, which flags the anomaly.
*   **`isolation_forest.py`**
    **Description:** Uses the `IsolationForest` algorithm from `scikit-learn`. It is efficient for finding outliers in high-dimensional data by isolating anomalies closer to the root of a decision tree.
*   **`lof_model.py`**
    **Description:** Implements Local Outlier Factor (LOF). It calculates the local density deviation of a given data point with respect to its neighbors.
*   **`hybrid_model.py`**
    **Description:** Combines the predictions of both the `IsolationForest` and the `Autoencoder`. If *either* model flags a network packet as an attack (an OR condition), the final output classifies it as an anomaly. This often boosts recall.
*   **`load_data.py`**
    **Description:** A utility script to load, explore, and pre-process the network traffic csv dataset. 

### Data Directory
*   **`data/`** 
    **Description:** Contains `traffic.csv`, which is the historical dataset used to train and test the ML models (like Autoencoder and Isolation Forest).

---

## 🚀 How to Run the Code

### Prerequisites
Before running any scripts, assure you have all necessary dependencies installed:

```bash
pip install flask pandas numpy scikit-learn torch scapy
```
*Note: Depending on your OS, `scapy` may require additional software such as [Npcap](https://npcap.com/) for Windows in order to capture live raw packets.*

### 1. Running the Live Network Dashboard (Real Traffic)
To monitor your actual local device network traffic in a web browser:

1. Open your terminal or command prompt **as Administrator/Root** (Required for live packet sniffing!).
2. Run the file:
   ```bash
   python live_app.py
   ```
3. Open your browser and navigate to `http://127.0.0.1:5000`. The page will refresh itself to keep stats updated.

### 2. Running the Simulated Dashboard (CSV Dataset)
To see how the Machine Learning model performs on the CSV data via the dashboard:

```bash
python app.py
```
Then visit `http://127.0.0.1:5000` in your web browser.

### 3. Running the CLI Live Packet Sniffer
To quickly test live network sniffing from your terminal without opening a web UI:

1. Open your terminal as **Administrator/Root**.
2. Run:
   ```bash
   python sniffer.py
   ```
3. You will start seeing `Normal` and `🚨 ANOMALY` traffic flowing into your console. Press `CTRL+C` to quit.

### 4. Running the Machine Learning Models
To train the models and see their classification reports directly:

```bash
python isolation_forest.py
python autoencoder.py
python hybrid_model.py
```
*(Ensure that `data/traffic.csv` is correctly placed inside the `data` folder before executing these)*
