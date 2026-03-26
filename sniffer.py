from scapy.all import sniff
import time

packet_count = 0
start_time = time.time()

def process_packet(packet):
    global packet_count, start_time

    packet_count += 1
    size = len(packet)
    proto = packet.proto if hasattr(packet, "proto") else 0

    # calculate packet rate
    current_time = time.time()
    elapsed = current_time - start_time

    if elapsed > 1:
        rate = packet_count / elapsed
        packet_count = 0
        start_time = current_time
    else:
        rate = 0

    # -------- SIMPLE ANOMALY RULES --------
    anomaly = False

    if size > 1000:          # very large packet
        anomaly = True

    if rate > 50:           # too many packets/sec
        anomaly = True

    # print result
    if anomaly:
        print(f"🚨 ANOMALY → Size: {size}, Proto: {proto}, Rate: {rate:.2f}")
    else:
        print(f"Normal → Size: {size}, Proto: {proto}, Rate: {rate:.2f}")

# start sniffing
sniff(prn=process_packet, store=0)