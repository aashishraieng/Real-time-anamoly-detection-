from flask import Flask, render_template_string
from scapy.all import sniff
import threading
import time

app = Flask(__name__)

# -------- SHARED DATA --------
live_data = []
ip_stats = {}

packet_count = 0
start_time = time.time()

# -------- PACKET PROCESSING --------
def process_packet(packet):
    global packet_count, start_time, ip_stats

    if not packet.haslayer("IP"):
        return

    src_ip = packet["IP"].src
    dst_ip = packet["IP"].dst

    size = len(packet)
    proto = packet.proto if hasattr(packet, "proto") else 0

    # track IP stats
    if src_ip not in ip_stats:
        ip_stats[src_ip] = {"count": 0, "bytes": 0}

    ip_stats[src_ip]["count"] += 1
    ip_stats[src_ip]["bytes"] += size

    # rate calculation
    packet_count += 1
    current_time = time.time()
    elapsed = current_time - start_time

    if elapsed > 1:
        rate = packet_count / elapsed
        packet_count = 0
        start_time = current_time
    else:
        rate = 0

    # -------- DETECTION --------
    anomaly = False
    reason = "Normal"

    if ip_stats[src_ip]["count"] > 50:
        anomaly = True
        reason = "High traffic from IP"

    elif size > 1200:
        anomaly = True
        reason = "Large packet"

    elif rate > 80:
        anomaly = True
        reason = "Possible flood"

    result = {
        "src": src_ip,
        "dst": dst_ip,
        "size": size,
        "proto": proto,
        "rate": round(rate, 2),
        "anomaly": anomaly,
        "status": "🚨" if anomaly else "Normal",
        "reason": reason
    }

    live_data.append(result)

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
        <meta http-equiv="refresh" content="3">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

        <style>
            body { font-family: Arial; text-align: center; }
            table { margin: auto; border-collapse: collapse; }
            th, td { border: 1px solid black; padding: 6px; }
        </style>
    </head>

    <body>

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

        <table>
            <tr>
                <th>Source IP</th>
                <th>Destination IP</th>
                <th>Size</th>
                <th>Protocol</th>
                <th>Rate</th>
                <th>Status</th>
                <th>Reason</th>
            </tr>

            {% for row in data %}
            <tr>
                <td>{{row.src}}</td>
                <td>{{row.dst}}</td>
                <td>{{row.size}}</td>
                <td>{{row.proto}}</td>
                <td>{{row.rate}}</td>
                <td>{{row.status}}</td>
                <td>{{row.reason}}</td>
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