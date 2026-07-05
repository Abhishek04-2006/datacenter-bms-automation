import streamlit as st
import sqlite3
import pandas as pd
import time
import random
import plotly.graph_objects as go
import os
from datetime import datetime

# 1. PAGE LAYOUT SETUP
st.set_page_config(page_title="Sify Tech Premium DCIM", layout="wide")

# Helper function to safely display logo without crashing container
def display_sify_logo(img_width=150):
    logo_path = "sify_logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=img_width)
    else:
        # Fallback branding badge if Docker sync delays the file
        st.markdown(f'<div style="background: linear-gradient(135deg, #00529b 0%, #002d5a 100%); color: white; padding: 6px 14px; border-radius: 4px; font-weight: bold; letter-spacing: 1px; display: inline-block; margin-bottom: 10px; font-size: 14px; border: 1px solid #0072ce;">SIFY TECHNOCRAFT DCIM</div>', unsafe_allow_html=True)

# 2. INDUSTRIAL SCADA THEME STYLING
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;700&display=swap');
    
    .stApp { background-color: #080c14 !important; font-family: 'Inter', sans-serif !important; color: #E2E8F0 !important; }
    .grid-banner { padding: 12px 20px; border-radius: 6px; font-weight: 700; margin-bottom: 20px; font-size: 0.85rem; letter-spacing: 0.5px; }
    .grid-ok { background-color: rgba(0, 255, 102, 0.05) !important; border: 1px solid #00FF66 !important; color: #00FF66 !important; }
    
    /* SCADA Floor Map Container Layout */
    .scada-floor-container {
        background: #0d1527;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 24px;
        box-shadow: inset 0 0 30px rgba(0,0,0,0.5);
    }
    
    /* Grid Aisle Layout Map */
    .dc-floor-grid {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
        background: #090f1d;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #1e293b;
        overflow-x: auto;
    }
    
    .aisle-column {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
    }
    
    .aisle-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: #64748b;
        font-weight: bold;
        margin-bottom: 4px;
    }
    
    /* Dynamic Hardware Racks */
    .scada-rack {
        width: 42px;
        height: 28px;
        border-radius: 4px;
        border: 1px solid rgba(255,255,255,0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        font-weight: bold;
        color: #000000;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .scada-rack:hover {
        transform: scale(1.12);
        box-shadow: 0 0 12px rgba(255,255,255,0.5);
        z-index: 10;
    }
    
    /* Inline Intermediate Row Temperature Sensors */
    .sensor-node {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin: 4px 0;
        box-shadow: 0 0 8px currentColor;
        transition: all 0.4s ease;
    }
    
    .insight-card { background: rgba(30, 41, 59, 0.4) !important; border-radius: 8px !important; padding: 15px !important; border: 1px solid rgba(255, 255, 255, 0.05) !important; margin-bottom: 10px !important; }
    .sidebar-alarm-card { background: rgba(255, 51, 51, 0.06) !important; border-left: 4px solid #FF3333 !important; padding: 12px; border-radius: 4px; margin-bottom: 12px; }
    </style>
""", unsafe_allow_html=True)

# 3. DATABASE SETUP & HISTORICAL LOGGING SCHEMA
db_path = "datacenter_telemetry.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS rack_telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rack_name TEXT NOT NULL,
    temperature REAL,
    load_kw REAL,
    humidity REAL,
    anomaly_status TEXT DEFAULT 'NORMAL',
    timestamp TEXT NOT NULL
)
""")
conn.commit()

# Setup Data Topology for 8 Full Rows (Aisle 1 to Aisle 8)
AISLES = {f"Aisle {i}": [f"{i}{ch}" for ch in ["A", "B", "C", "D", "E", "F", "G", "H"]] for i in range(1, 9)}

# Generate live streaming telemetry records smoothly on each refresh cycle
current_time_str = datetime.now().strftime("%H:%M:%S")

for aisle_name, racks in AISLES.items():
    for rack_id in racks:
        rand_temp = round(random.uniform(20.5, 29.8), 1)
        rand_load = round(random.uniform(3.0, 6.5), 1)
        rand_hum = round(random.uniform(40.0, 50.0), 1)
        status = "CRITICAL" if rand_temp > 28.0 else "NORMAL"
        
        cursor.execute("""
        INSERT INTO rack_telemetry (rack_name, temperature, load_kw, humidity, anomaly_status, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (rack_id, rand_temp, rand_load, rand_hum, status, current_time_str))
conn.commit()

# Prevent memory leaks: Keep only latest 1500 rows for charts performance
cursor.execute("DELETE FROM rack_telemetry WHERE id NOT IN (SELECT id FROM rack_telemetry ORDER BY id DESC LIMIT 1500)")
conn.commit()


# 4. SIDEBAR NAVIGATION PANELS
st.sidebar.title("⚙️ SCADA Matrix Portal")
page = st.sidebar.radio("Navigation Console", ["🏢 Blueprint Spatial Floor Plan", "📊 Live SCADA Matrix Monitor"])
auto_refresh = st.sidebar.checkbox("Enable 3s Telemetry Update Loop", value=True)

# Dynamic Sidebar Alarm Center
st.sidebar.subheader("🚨 Active Critical Hotspots")
cursor.execute("SELECT rack_name, temperature FROM rack_telemetry WHERE temperature > 28.0 ORDER BY id DESC LIMIT 4")
active_alarms = cursor.fetchall()
if active_alarms:
    for alarm in active_alarms:
        st.sidebar.markdown(f"<div class='sidebar-alarm-card'><strong>Rack {alarm[0]} Alert</strong><br/>Sensor Critical: <span style='color:#FF3333;'>{alarm[1]}°C</span></div>", unsafe_allow_html=True)
else:
    st.sidebar.success("✅ Airflow Terminals Nominal")

main_workspace = st.container()

# ==========================================
# TAB 1: BLUEPRINT SPATIAL FLOOR PLAN
# ==========================================
if page == "🏢 Blueprint Spatial Floor Plan":
    with main_workspace:
        display_sify_logo(img_width=150)
        st.header("🏢 Live Spatial Data Center Matrix Blueprint")
        st.write("Real-Time Telemetry Maps with Row Temperature Flow Interceptor Nodes")
        
        floor_html = '<div class="scada-floor-container"><div class="dc-floor-grid">'
        
        for aisle_num in range(1, 9):
            aisle_name = f"Aisle {aisle_num}"
            floor_html += f'<div class="aisle-column"><div class="aisle-label">ROW {aisle_num}</div>'
            
            for r_idx, name in enumerate(AISLES[aisle_name]):
                cursor.execute('SELECT temperature, anomaly_status FROM rack_telemetry WHERE rack_name = ? ORDER BY id DESC LIMIT 1', (name,))
                data_row = cursor.fetchone()
                temp = data_row[0] if data_row else 22.0
                
                if temp > 28.0:
                    bg_color = "#FF3333"
                    text_color = "#FFFFFF"
                elif temp > 25.0:
                    bg_color = "#FFAA00"
                    text_color = "#000000"
                else:
                    bg_color = "#00FF66"
                    text_color = "#000000"
                
                floor_html += f'''
                <div class="scada-rack" style="background-color: {bg_color}; color: {text_color};" 
                     title="Rack Terminal: {name}&#10;Live Temperature: {temp}°C">
                    {name}
                </div>
                '''
                
                if r_idx < len(AISLES[aisle_name]) - 1:
                    sensor_id = f"S-{aisle_num}{r_idx}"
                    sensor_color = "#FF3333" if temp > 28.0 else "#00FF66"
                    floor_html += f'<div class="sensor-node" style="color: {sensor_color}; background-color: {sensor_color};" title="Inline Thermal Sensor: {sensor_id}"></div>'
            
            floor_html += '</div>'
            
        floor_html += '</div></div>'
        st.markdown(floor_html, unsafe_allow_html=True)

# ==========================================
# TAB 2: DETAILED DATA MATRIX & LIVE TREND CHARTS
# ==========================================
elif page == "📊 Live SCADA Matrix Monitor":
    with main_workspace:
        display_sify_logo(img_width=120)
        st.markdown('<div class="grid-banner grid-ok">🟢 SCADA BROADCAST ACTIVE — HISTORICAL METRIC ANALYTICS CONTAINER ONLINE</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("⚡ Datacenter Grid Row Overview Matrix")
            selected_aisle = st.selectbox("Select Target Row Array to Analyze", list(AISLES.keys()))
            
            rack_data = []
            for name in AISLES[selected_aisle]:
                cursor.execute('SELECT temperature, load_kw, humidity, anomaly_status FROM rack_telemetry WHERE rack_name = ? ORDER BY id DESC LIMIT 1', (name,))
                r = cursor.fetchone()
                if r:
                    rack_data.append({"Rack": name, "Temp (°C)": r[0], "Load (kW)": r[1], "Humidity (%)": r[2], "Status": r[3]})
            
            if rack_data:
                df_racks = pd.DataFrame(rack_data)
                st.dataframe(df_racks.set_index("Rack"), use_container_width=True)
        
        with col2:
            st.subheader("📈 Quick Infrastructure Diagnostics")
            cursor.execute("SELECT AVG(temperature), SUM(load_kw) FROM rack_telemetry WHERE id IN (SELECT id FROM rack_telemetry ORDER BY id DESC LIMIT 64)")
            summary = cursor.fetchone()
            avg_temp = round(summary[0], 1) if summary[0] else 22.4
            total_load = round(summary[1], 1) if summary[1] else 420.5
            
            st.markdown(f"""
            <div class='insight-card'>
                <small style='color:#94A3B8;'>AVG CORE AIRFLOW TEMP</small>
                <h2>{avg_temp} °C</h2>
            </div>
            <div class='insight-card'>
                <small style='color:#94A3B8;'>TOTAL FACILITY REAL-LOAD</small>
                <h2>{total_load} kW</h2>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # --- DYNAMIC HISTORICAL GRAPH SECTION ---
        st.subheader("📊 Real-Time Thermal Chrono-Trend Tracking")
        
        all_racks_list = []
        for a in AISLES.values():
            all_racks_list.extend(a)
            
        target_rack = st.selectbox("🎯 Select Specific Rack Node to Plot Trend History", all_racks_list, index=0)
        
        history_df = pd.read_sql_query(
            "SELECT temperature, load_kw, timestamp FROM rack_telemetry WHERE rack_name = ? ORDER BY id ASC", 
            conn, params=(target_rack,)
        )
        
        if not history_df.empty:
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=history_df['timestamp'], y=history_df['temperature'],
                mode='lines+markers', name='Temperature (°C)',
                line=dict(color='#FF3333', width=3),
                marker=dict(size=6)
            ))
            
            fig.add_trace(go.Scatter(
                x=history_df['timestamp'], y=history_df['load_kw'],
                mode='lines+markers', name='Load (kW)',
                line=dict(color='#00FF66', width=2, dash='dash'),
                marker=dict(size=4)
            ))
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(13,21,39,0.5)',
                margin=dict(l=20, r=20, t=10, b=20),
                height=350,
                xaxis=dict(
                    title="Timeline (HH:MM:SS)", 
                    gridcolor='#1e293b', 
                    tickfont=dict(color='#64748b'),
                    titlefont=dict(color='#64748b')
                ),
                yaxis=dict(
                    title="Value Scale", 
                    gridcolor='#1e293b', 
                    tickfont=dict(color='#64748b'),
                    titlefont=dict(color='#64748b')
                ),
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(color='#e2e8f0')
                ),
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Gathering historical data packets... Graph will generate shortly.")

# 5. REFRESH LOOP EXECUTION
if auto_refresh:
    time.sleep(3)
    st.rerun()