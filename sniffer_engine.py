from scapy.all import sniff
import threading
import time

class NetworkMonitor:
    def __init__(self):
        self.is_sniffing = False
        self.flows = {} # Key: flow_tuple, Value: flow_stats dict
        self.anomalies = []
        self.max_history = 100
        self.thread = None

    def start(self):
        if not self.is_sniffing:
            self.is_sniffing = True
            if self.thread is None or not self.thread.is_alive():
                self.thread = threading.Thread(target=self._sniff_loop, daemon=True)
                self.thread.start()

    def stop(self):
        self.is_sniffing = False
    
    def _sniff_loop(self):
        sniff(prn=self.process_packet, store=0)

    def process_packet(self, packet):
        if not self.is_sniffing:
            return

        if not packet.haslayer("IP"):
            return

        ip_layer = packet["IP"]
        src_ip = ip_layer.src
        dst_ip = ip_layer.dst

        # Get ports if TCP/UDP
        src_port = 0
        dst_port = 0
        protocol_name = "OTHER"

        if packet.haslayer("TCP"):
            src_port = packet["TCP"].sport
            dst_port = packet["TCP"].dport
            protocol_name = "TCP"
        elif packet.haslayer("UDP"):
            src_port = packet["UDP"].sport
            dst_port = packet["UDP"].dport
            protocol_name = "UDP"
        
        protocol_num = packet.proto if hasattr(ip_layer, "proto") else 0
        size = len(packet)
        current_time = time.time()

        flow_key = (src_ip, src_port, dst_ip, dst_port, protocol_name)

        if flow_key not in self.flows:
            self.flows[flow_key] = {
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "src_port": src_port,
                "dst_port": dst_port,
                "protocol": protocol_name,
                "start_time": current_time,
                "end_time": current_time,
                "duration": 0,
                "packets": 0,
                "bytes": 0,
                "packets_per_sec": 0,
                "bytes_per_sec": 0,
                "is_anomaly": False,
                "reason": ""
            }

        flow = self.flows[flow_key]
        flow["packets"] += 1
        flow["bytes"] += size
        flow["end_time"] = current_time
        
        duration = flow["end_time"] - flow["start_time"]
        flow["duration"] = round(duration, 2)

        if duration > 0:
            flow["packets_per_sec"] = round(flow["packets"] / duration, 2)
            flow["bytes_per_sec"] = round(flow["bytes"] / duration, 2)
        else:
            flow["packets_per_sec"] = 0
            flow["bytes_per_sec"] = 0

        # Heuristic Anomaly Detection on the Flow
        anomaly = False
        reason = ""

        if flow["packets_per_sec"] > 200:
            anomaly = True
            reason = "High Packet Rate (Flood Warning)"
        elif size > 2000:
            anomaly = True
            reason = "Oversized Packet Detected"
        elif flow["bytes_per_sec"] > 500000: # 500 KB/s
            anomaly = True
            reason = "High Bandwidth Consumption"

        if anomaly:
            flow["is_anomaly"] = True
            flow["reason"] = reason
            
            # Record it in anomalies list (avoid duplicates from same flow updating constantly, maybe just last 50)
            anomaly_record = flow.copy()
            anomaly_record['timestamp'] = current_time
            self.anomalies.insert(0, anomaly_record)
            if len(self.anomalies) > 50:
                self.anomalies.pop()

    def get_live_flows(self, limit=50):
        # Return sorted by end_time descending
        sorted_flows = sorted(self.flows.values(), key=lambda x: x["end_time"], reverse=True)
        return sorted_flows[:limit]

    def get_attacks(self):
        return self.anomalies

# Singleton instance
monitor = NetworkMonitor()
