# 🏢 Hyperscale Data Center - BMS Automation & PUE Optimization Engine

An enterprise-grade, event-driven Building Management System (BMS) simulation designed to mimic real-time industrial IoT telemetry, automated climate control loops, and environmental efficiency tracking ($PUE$) typical of hyperscale data center operations.

## 🛠️ System Architecture & Workflow
The platform utilizes an asynchronous, decoupled event-driven architecture to communicate telemetry streams across the cloud:

1. **Telemetry Simulation Edge:** `rack_sensor.py` acts as a smart server rack hardware agent, broadcasting live thermal and power consumption metrics via the MQTT protocol.
2. **Core Automation Engine:** `bms_brain.py` processes raw incoming payload streams, implements exception handling routines for packet parsing resilience, calculates Power Usage Effectiveness ($PUE$), and manages data persistence layers.
3. **Observability Dashboard:** `bms_dashboard.py` stands up a real-time visual web presentation layer built on Streamlit, allowing operators to oversee facility efficiency metrics and execute two-way manual overrides.

## 🚀 Technical Core Competencies Demonstrated
* **Event-Driven Pub/Sub Design:** Asynchronous data distribution handled over cloud brokers using the standard MQTT protocol.
* **Fault-Tolerant System Architecture:** Built-in programmatic safety nets (`try-except` wrappers) ensuring execution runtime resilience against corrupted sensor telemetry packets.
* **Self-Healing Network Connectivity:** Non-blocking background threading control implementations allowing instant connection restoration upon unexpected network disconnections.
* **Infrastructure Math Operations:** Automation algorithms that compute real-time operational efficiency ratings ($PUE$).

## 🏃 How to Run the Platform Locally

1. **Install Dependencies:**
   ```bash
   python -m pip install paho-mqtt streamlit