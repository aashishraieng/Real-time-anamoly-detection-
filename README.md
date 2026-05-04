# Real-Time Network Anomaly Detection System

This repository contains a comprehensive suite of tools and machine learning models for detecting anomalies in network traffic. It has been recently unified into a single, high-performance web dashboard that provides real-time network traffic sniffing, heuristic attack detection, and offline machine learning model evaluation.
    
A comprehensive suite of tools and machine learning models for detecting anomalies in network traffic. This project combines real-time packet sniffing, heuristic attack detection, and offline machine learning evaluation into a single unified dashboard.

## Features

- Real-time network traffic sniffing using `scapy`.
- Heuristic anomaly detection for floods, oversized packets, and high bandwidth usage.
- Offline machine learning evaluation on historical traffic data.
- Support for multiple ML models:
  - Isolation Forest.
  - Local Outlier Factor (LOF).
  - Autoencoder.
  - Hybrid model.
- Web dashboard for live flow monitoring and attack history.
- CSV upload support for offline anomaly scanning.

## Project Structure

### Unified Web Dashboard
| File / Folder | Description |
|---|---|
| `main.py` | Central Flask application that hosts the web dashboard and REST API endpoints. |
| `sniffer_engine.py` | Background engine for real-time packet sniffing, flow aggregation, and heuristic detection. |
| `ml_evaluator.py` | Machine learning backend for training, evaluating, and scanning network traffic data. |
| `static/` | CSS, JavaScript, and other front-end assets. |
| `templates/` | HTML templates for the dashboard UI. |

### Legacy / Standalone Scripts
| File | Description |
|---|---|
| `live_app.py` | Older live-sniffing dashboard version. |
| `app.py` | CSV-based simulation dashboard for visual testing. |
| `sniffer.py` | CLI packet sniffer that prints anomaly alerts in the terminal. |
| `autoencoder.py` | Standalone Autoencoder training and evaluation script. |
| `isolation_forest.py` | Standalone Isolation Forest training and evaluation script. |
| `lof_model.py` | Standalone Local Outlier Factor training and evaluation script. |
| `hybrid_model.py` | Standalone hybrid model combining multiple detectors. |
| `load_data.py` | Utility for loading, exploring, and preprocessing the dataset. |

### Data Directory
| File | Description |
|---|---|
| `data/traffic.csv` | Historical traffic dataset used for training and testing ML models. |

## Detection Approaches

### Heuristic Engine
The heuristic engine in `sniffer_engine.py` applies rule-based thresholds to detect obvious attacks instantly. It is designed to flag conditions such as packet floods, oversized packets, and unusually high bandwidth consumption.

### Isolation Forest
Isolation Forest is a tree-based anomaly detection algorithm that isolates outliers quickly and works well for high-dimensional data.

### Local Outlier Factor
LOF detects anomalies by comparing the local density of each data point against its neighbors. It is useful for identifying points that look unusual in dense regions.

### Autoencoder
The Autoencoder is trained on normal traffic only. When abnormal traffic is processed, the reconstruction error increases, which helps identify anomalies.

### Hybrid Model
The Hybrid Model combines predictions from the Isolation Forest and Autoencoder. If either model flags a sample as anomalous, it is classified as an attack to improve recall.

## Prerequisites

Install the required Python packages:

```bash
pip install flask pandas numpy scikit-learn torch scapy
```

> Note: On Windows, `scapy` may require [Npcap](https://npcap.com/) for live packet capture.

## Running the Project

### 1. Unified Web Dashboard
```bash
python main.py
```

Then open:

```bash
http://127.0.0.1:5000
```

From the dashboard, you can:
- Start or stop live sniffing.
- View real-time traffic flows.
- Inspect attack history.
- Run ML model evaluations.
- Upload CSV files for offline anomaly scanning.

### 2. CLI Live Packet Sniffer
```bash
python sniffer.py
```

This prints `Normal` and `🚨 ANOMALY` messages directly in the terminal.

### 3. Standalone ML Models
```bash
python isolation_forest.py
python autoencoder.py
python hybrid_model.py
```

Make sure `data/traffic.csv` is present before running these scripts.

## Usage Notes

- Run live sniffing commands with administrator/root privileges.
- Ensure your dataset is cleaned and formatted correctly before training.
- The dashboard is intended for real-time monitoring and offline model comparison.
- Heuristic detection is immediate, while ML-based detection is better for deeper analysis.

## Contributing

Contributions are welcome. If you want to improve the project, you can:
- Fix bugs.
- Improve detection accuracy.
- Add new anomaly detection models.
- Enhance the dashboard UI.
- Improve preprocessing and evaluation pipelines.

### Contribution Steps
1. Fork the repository.
2. Create a new branch for your feature or fix.
3. Make your changes.
4. Test the project locally.
5. Submit a pull request with a clear description.


## Acknowledgements

- `Flask` for the web dashboard.
- `Scapy` for packet sniffing.
- `PyTorch` for the Autoencoder implementation.
- `scikit-learn` for classical anomaly detection models.
