import paho.mqtt.client as mqtt
import time

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "sify_bms_project_abhishek/rack1/metrics"

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("🟢 [NETWORK STATUS] Successfully connected to cloud broker!")
        client.subscribe(TOPIC)
    else:
        print(f"🔴 [NETWORK STATUS] Connection failed: {rc}")

def on_disconnect(client, userdata, disconnect_flags, rc, properties=None):
    print("⚠️ [NETWORK ALERT] Disconnected! Re-connecting automatically...")

def on_message(client, userdata, message):
    try:
        data_string = message.payload.decode("utf-8")
        
        # Parse text values (e.g., "temperature=26.40,power=5.30")
        parts = data_string.split(",")
        temp = float(parts[0].split("=")[1])
        it_power = float(parts[1].split("=")[1]) # This is our IT Equipment Power
        
        # --- INFRASTRUCTURE MATH ENGINE ---
        # Calculate dynamic cooling overhead based on current temperature
        if temp > 28.0:
            cooling_power = 6.5  # Chillers running at max speed draw massive power
            chiller_status = "MAX_SPEED"
        else:
            cooling_power = 2.1  # Chillers running at baseline power
            chiller_status = "BASELINE"
            
        total_facility_power = it_power + cooling_power
        pue = round(total_facility_power / it_power, 2)
        
        print(f"📥 Data Received -> Temp: {temp}°C | IT Load: {it_power}kW | Chiller: {chiller_status}")
        print(f"📊 [EFFICIENCY METRICS] Total Power: {total_facility_power}kW | Calculated PUE: {pue}")
        
        # --- AUTOMATED EFFICIENCY ALERT RULE ---
        if pue > 1.50:
            print(f"❌ [ALERT] Efficiency Spike! PUE is {pue} (Threshold > 1.50). Wasting excess energy on cooling!")
        else:
            print(f"✨ [OPTIMAL] Green Facility Status! PUE is healthy at {pue}.")
        print("-" * 60)
            
        # Write the updated calculated records to our text database file
        # Format: temperature, it_power, cooling_power, total_power, pue
        log_payload = f"temperature={temp},power={it_power},cooling={cooling_power},total={total_facility_power},pue={pue}"
        with open("datacenter_logs.txt", "a") as f:
            f.write(f"{log_payload}\n")

    except Exception as e:
        print(f"❌ [BMS ERROR] Parsing/Math failure: {e}")

receiver = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
receiver.on_connect = on_connect
receiver.on_disconnect = on_disconnect
receiver.on_message = on_message

print("🧠 BMS Automation Engine with PUE Math Core Booting...")
receiver.connect(BROKER, PORT)
receiver.loop_start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("🔌 Core offline.")
    receiver.loop_stop()