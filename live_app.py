from flask import Flask, render_template_string
from scapy.all import sniff
import threading
import time

app = Flask(__name__)

# -------- SHARED DATA --------
live_data = []

# -------- PACKET PROCESSING --------
packet_count = 0
start_time = time.time()

def process_packet(packet):
    global packet_count, start_time

    packet_count += 1
    size = len(packet)
    proto = packet.proto if hasattr(packet, "proto") else 0

    current_time = time.time()
    elapsed = current_time - start_time

    if elapsed > 1:
        rate = packet_count / elapsed
        packet_count = 0
        start_time = current_time
    else:
        rate = 0

    anomaly = False

    if size > 1000:
        anomaly = True
    if rate > 50:
        anomaly = True

    result = {
        "size": size,
        "proto": proto,
        "rate": round(rate, 2),
        "anomaly": anomaly
    }

    live_data.append(result)

    # keep last 50 entries only
    if len(live_data) > 50:
        live_data.pop(0)

# -------- SNIFFER THREAD --------
def start_sniffer():
    sniff(prn=process_packet, store=0)

# -------- DASHBOARD --------
@app.route("/")
def home():

    anomalies = sum(1 for x in live_data if x["anomaly"])
    normal = len(live_data) - anomalies

    return render_template_string("""
    <html>
    <head>
        <title>Live Network Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>

    <body style="font-family: Arial; text-align: center;">

        <h1>🔥 Live Network Anomaly Detection</h1>

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
                        label: 'Live Traffic',
                        data: [{{normal}}, {{anomalies}}],
                    }]
                }
            });
        </script>

        <h2>Recent Packets</h2>

        <table border="1" style="margin:auto;">
            <tr>
                <th>Size</th>
                <th>Protocol</th>
                <th>Rate</th>
                <th>Status</th>
            </tr>

            {% for row in data %}
            <tr>
                <td>{{row.size}}</td>
                <td>{{row.proto}}</td>
                <td>{{row.rate}}</td>
                <td>
                    {% if row.anomaly %}
                        🚨
                    {% else %}
                        Normal
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>

    </body>
    </html>
    """, data=live_data[::-1], anomalies=anomalies, normal=normal)

# -------- MAIN --------
if __name__ == "__main__":
    threading.Thread(target=start_sniffer, daemon=True).start()
    app.run(debug=True)