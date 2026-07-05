import time
import sqlite3
from pyModbusTCP.client import ModbusClient

DB_FILE = "datacenter.db"

AISLES = {
    "Aisle 1": [f"1{c}" for c in ["A","B","C","D","E","F","G","H"]],
    "Aisle 2": [f"2{c}" for c in ["A","B","C","D","E","F","G","H"]],
    "Aisle 3": [f"3{c}" for c in ["A","B","C","D","E","F","G","H"]],
    "Aisle 4": [f"4{c}" for c in ["A","B","C","D","E","F","G","H"]],
    "Aisle 5": [f"5{c}" for c in ["A","B","C","D","E","F","G","H","J","K","L","M"]],
    "Aisle 6": [f"6{c}" for c in ["A","B","C","D","E","F","G","H","J","K","L","M"]],
    "Aisle 7": [f"7{c}" for c in ["A","B","C","D","E","F","G","H","J","K","L","M"]],
    "Aisle 8": [f"8{c}" for c in ["A","B","C","D","E","F","G","H","J","K","L","M"]]
}

ALL_FACILITY_RACKS = [rack for list_racks in AISLES.values() for rack in list_racks]

# Bind client to our internal Docker network service hostname name
client = ModbusClient(host='field_layer', port=5020, auto_open=True, auto_close=True)

def init_scada_tables():
    """Guarantees the schema state exists inside clean Docker volumes"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. Telemetry table configuration
    cursor.execute('''CREATE TABLE IF NOT EXISTS rack_telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        rack_name TEXT, 
        temperature REAL, 
        power_draw REAL, 
        humidity REAL, 
        pue REAL, 
        anomaly_status TEXT DEFAULT 'NORMAL'
    )''')
    
    # 2. Control state configuration
    cursor.execute('''CREATE TABLE IF NOT EXISTS facility_status (
        id INTEGER PRIMARY KEY, 
        grid_state TEXT DEFAULT 'ONLINE', 
        dg_fuel_tank_01 REAL DEFAULT 4400.0,
        dg_fuel_tank_02 REAL DEFAULT 4600.0, 
        ups_soc REAL DEFAULT 100.0, 
        chiller_vfd_speed REAL DEFAULT 50.0, 
        override_mode INTEGER DEFAULT 0, 
        override_speed REAL DEFAULT 50.0
    )''')
    
    # Seed default rows if empty
    cursor.execute("SELECT COUNT(*) FROM facility_status")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""INSERT INTO facility_status 
            (grid_state, dg_fuel_tank_01, dg_fuel_tank_02, ups_soc, chiller_vfd_speed, override_mode, override_speed) 
            VALUES ('ONLINE', 4400.0, 4600.0, 100.0, 50.0, 0, 50.0)""")
            
    conn.commit()
    conn.close()

# Run the initialization check before booting pipeline listeners
init_scada_tables()

# Keep track of active emergency load-shedded aisles
shedded_aisles = set()

print("🚀 [SCADA INTERLOCK CORE] Safety Automation Pipeline Engaged...")
while True:
    batch_1 = client.read_holding_registers(0, 120)
    batch_2 = client.read_holding_registers(120, 120)
    
    if batch_1 and batch_2:
        response = batch_1 + batch_2
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT override_mode, override_speed FROM facility_status WHERE id = 1")
        override_row = cursor.fetchone()
        override_mode, override_speed = override_row if override_row else (0, 50.0)
        
        # Temporary storage to compute real-time averages across aisles
        aisle_temps = {k: [] for k in AISLES.keys()}
        rack_data_map = {}
        
        # Parse registers first
        for index, label in enumerate(ALL_FACILITY_RACKS):
            base_idx = index * 3
            temp = response[base_idx] / 100.0
            power = response[base_idx + 1] / 100.0
            humidity = response[base_idx + 2] / 100.0
            
            # Identify which aisle this rack belongs to
            for aisle_name, rack_list in AISLES.items():
                if label in rack_list:
                    aisle_temps[aisle_name].append(temp)
                    break
            
            rack_data_map[label] = {"temp": temp, "power": power, "humidity": humidity}
            
        # Evaluate Load Shedding Interlocks Aisle by Aisle
        for aisle_name, temps in aisle_temps.items():
            avg_aisle_temp = sum(temps) / len(temps) if temps else 0.0
            
            # TRIGGER CONDITION: Aisle breaches 30°C
            if avg_aisle_temp > 30.0 and aisle_name not in shedded_aisles:
                shedded_aisles.add(aisle_name)
                print(f"🚨 [CRITICAL GRID INTERLOCK] {aisle_name} Avg Temp reached {avg_aisle_temp:.2f}°C! SHEDDING POWER LOAD AUTOMATICALLY...")
                
            # RECOVERY CONDITION: Aisle drops back safely below 25°C
            elif avg_aisle_temp < 25.0 and aisle_name in shedded_aisles:
                shedded_aisles.remove(aisle_name)
                print(f"🟢 [GRID INTERLOCK RECOVERY] {aisle_name} stabilized at {avg_aisle_temp:.2f}°C. Re-engaging IT workloads.")

        # Commit filtered metrics to Database
        peak_room_temp = 0.0
        for label, data in rack_data_map.items():
            temp = data["temp"]
            humidity = data["humidity"]
            
            # Find parent aisle
            parent_aisle = None
            for aisle_name, rack_list in AISLES.items():
                if label in rack_list:
                    parent_aisle = aisle_name
                    break
            
            # If the aisle is currently load-shedded, force compute draw to 0.0 kW
            if parent_aisle in shedded_aisles:
                power = 0.0
                anomaly_status = "LOAD_SHEDDED"
            else:
                power = data["power"]
                anomaly_status = "CRITICAL" if temp > 28.0 else "NORMAL"
                
            if temp > peak_room_temp:
                peak_room_temp = temp
                
            active_vfd = override_speed if override_mode == 1 else (95.0 if temp > 28.0 else 50.0)
            pue = 1.00 if power == 0.0 else round((power + ((active_vfd/100.0)*(power*0.35))) / power, 2)
            
            cursor.execute('''INSERT INTO rack_telemetry 
                (rack_name, temperature, power_draw, humidity, pue, anomaly_status) 
                VALUES (?, ?, ?, ?, ?, ?)''', (label, temp, power, humidity, pue, anomaly_status))
            
        vfd_final = override_speed if override_mode == 1 else (95.0 if peak_room_temp > 28.0 else 50.0)
        cursor.execute("UPDATE facility_status SET chiller_vfd_speed = ? WHERE id = 1", (vfd_final,))
        
        conn.commit()
        conn.close()
    
    time.sleep(2)