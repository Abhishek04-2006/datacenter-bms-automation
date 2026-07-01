import streamlit as st
import time
import paho.mqtt.client as mqtt

st.set_page_config(page_title="Sify BMS Automation Dashboard", layout="wide")
st.title("🏢 Sify Data Center - Advanced BMS Efficiency Dashboard")

st.sidebar.header("🛠️ Manual Facility Override")
if st.sidebar.button("🚨 TRIGGER EMERGENCY COOLING OVERRIDE"):
    try:
        control_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        control_client.connect("broker.hivemq.com", 1883)
        control_client.publish("sify_bms_project_abhishek/rack1/control", "OVERRIDE_ON")
        st.sidebar.success("⚡ Emergency Command Sent!")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

placeholder = st.empty()

while True:
    with placeholder.container():
        try:
            with open("datacenter_logs.txt", "r") as f:
                lines = f.readlines()
            
            if lines:
                # Parse the new fields out from the latest entry line
                latest_data = lines[-1].strip()
                items = latest_data.split(",")
                
                temp = float(items[0].split("=")[1])
                it_power = float(items[1].split("=")[1])
                cooling_power = float(items[2].split("=")[1])
                total_power = float(items[3].split("=")[1])
                pue = float(items[4].split("=")[1])
                
                # Top Row Cards: Primary Metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(label="🌡️ Rack Temperature", value=f"{temp} °C")
                with col2:
                    st.metric(label="⚡ IT Equipment Load", value=f"{it_power} kW")
                with col3:
                    st.metric(label="❄️ Cooling System Power", value=f"{cooling_power} kW")
                with col4:
                    # Highlight PUE card based on value condition status
                    if pue > 1.50:
                        st.metric(label="📊 Facility PUE STATUS", value=pue, delta="High Energy Waste", delta_color="inverse")
                    else:
                        st.metric(label="📊 Facility PUE STATUS", value=pue, delta="Optimal Efficiency")

                # Layout warnings or success messages based on calculated thresholds
                if pue > 1.50:
                    st.error(f"🚨 ALERT: Facility PUE is critical ({pue})! Cooling load overhead is consuming too much power relative to computing throughput.")
                else:
                    st.success(f"🟢 Facility is operating within green targets. Current Power Usage Effectiveness score: {pue}")
                        
                st.subheader("📋 Live Facility Logs")
                st.text("\n".join(lines[-8:]))
        except Exception as e:
            st.warning(f"Syncing with metrics database engine logs... ({e})")

    time.sleep(1)