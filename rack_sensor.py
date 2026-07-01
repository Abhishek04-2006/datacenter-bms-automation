import time
import random
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_METRICS = "sify_bms_project_abhishek/rack1/metrics"
TOPIC_CONTROL = "sify_bms_project_abhishek/rack1/control"

# Track override state
emergency_cooling_active = False

# This runs if the dashboard sends a control command string
def on_message(client, userdata, message):
    global emergency_cooling_active
    command = message.payload.decode("utf-8")
    if command == "OVERRIDE_ON":
        print("🚨 [RECEIVED OVERRIDE COMMAND] Dashboard triggered emergency fans! Dropping temps...")
        emergency_cooling_active = True

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message

client.connect(BROKER, PORT)
# Listen to the control topic for commands
client.subscribe(TOPIC_CONTROL)
client.loop_start() # Run message receiver thread in the background

print("🚀 Smart Sensor Listening for Override commands... Press Ctrl+C to stop.")

while True:
    if emergency_cooling_active:
        # Generate lower, cooled down temperatures since fans are forced to 100%
        temperature = round(random.uniform(16.0, 21.0), 2)
        power_draw = round(random.uniform(8.5, 11.0), 2) # Fans draw more power
        # Reset override flag after cooling down for demonstration
        emergency_cooling_active = False 
    else:
        # Normal fluctuating temperature values
        temperature = round(random.uniform(22.0, 32.0), 2)
        power_draw = round(random.uniform(4.5, 8.0), 2)
    
    payload = f"temperature={temperature},power={power_draw}"
    client.publish(TOPIC_METRICS, payload)
    print(f"📡 Sent data to Cloud Broker: {payload}")
    
    time.sleep(2)