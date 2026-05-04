from flask import Flask, jsonify, request, render_template
from sniffer_engine import monitor
from ml_evaluator import evaluator
import os
import threading

app = Flask(__name__)

# Start monitor in stopped state (no thread yet, user has to press play)
# Let's keep it stopped by default so it doesn't run without user consenting via UI

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/sniffer/toggle", methods=["POST"])
def toggle_sniffer():
    data = request.json
    action = data.get("action") # 'start' or 'stop'
    
    if action == "start":
        monitor.start()
        return jsonify({"status": "running"})
    elif action == "stop":
        monitor.stop()
        return jsonify({"status": "stopped"})
    return jsonify({"error": "Invalid action"}), 400

@app.route("/api/sniffer/status", methods=["GET"])
def sniffer_status():
    return jsonify({"is_sniffing": monitor.is_sniffing})

@app.route("/api/traffic/live", methods=["GET"])
def get_live_traffic():
    flows = monitor.get_live_flows(limit=50)
    return jsonify(flows)

@app.route("/api/traffic/attacks", methods=["GET"])
def get_attack_traffic():
    attacks = monitor.get_attacks()
    return jsonify(attacks)

@app.route("/api/models/eval", methods=["POST"])
def get_model_eval():
    data = request.json
    model_name = data.get("model_name")
    if not model_name:
        return jsonify({"error": "model_name required"}), 400
    
    # Run evaluation in a background thread or synchronously?
    # For now synchronous, but cached so it's fast after first time
    metrics = evaluator.evaluate_model(model_name)
    return jsonify(metrics)

@app.route("/api/csv/upload", methods=["POST"])
def upload_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file and file.filename.endswith(".csv"):
        result = evaluator.offline_csv_eval(file)
        return jsonify(result)
        
    return jsonify({"error": "Invalid file type. Must be .csv"}), 400

if __name__ == "__main__":
    app.run(debug=True, port=5000)
