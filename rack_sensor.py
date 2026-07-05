import time
import random
from pyModbusTCP.server import ModbusServer

# Spin up our industrial server layout panel matrix
server = ModbusServer(host='0.0.0.0', port=5020, no_block=True)

# Replicating all structural rows matching the blueprint visual canvas layout
RACKS_AISLE_1 = [f"1{ch}" for ch in ["A","B","C","D","E","F","G","H"]]
RACKS_AISLE_2 = [f"2{ch}" for ch in ["A","B","C","D","E","F","G","H"]]
RACKS_AISLE_3 = [f"3{ch}" for ch in ["A","B","C","D","E","F","G","H"]]
RACKS_AISLE_4 = [f"4{ch}" for ch in ["A","B","C","D","E","F","G","H"]]
RACKS_AISLE_5 = [f"5{ch}" for ch in ["A","B","C","D","E","F","G","H","J","K","L","M"]]
RACKS_AISLE_6 = [f"6{ch}" for ch in ["A","B","C","D","E","F","G","H","J","K","L","M"]]
RACKS_AISLE_7 = [f"7{ch}" for ch in ["A","B","C","D","E","F","G","H","J","K","L","M"]]
RACKS_AISLE_8 = [f"8{ch}" for ch in ["A","B","C","D","E","F","G","H","J","K","L","M"]]

ALL_FACILITY_RACKS = RACKS_AISLE_1 + RACKS_AISLE_2 + RACKS_AISLE_3 + RACKS_AISLE_4 + RACKS_AISLE_5 + RACKS_AISLE_6 + RACKS_AISLE_7 + RACKS_AISLE_8

try:
    print(f"🟢 [SCADA FIELD LAYER] Modbus TCP Server Online. Provisioning registers for ALL {len(ALL_FACILITY_RACKS)} racks...")
    server.start()
    
    while True:
        registers_to_write = []
        
        for name in ALL_FACILITY_RACKS:
            # High-density server spaces get random spikes above 28°C to test the red blinking lights
            if name[0] in ["1", "5", "8"] and random.choice([True, False, False, False]):
                temp = random.uniform(28.2, 31.5)
            else:
                temp = random.uniform(20.0, 24.8)
                
            power = random.uniform(4.0, 12.5)
            hum = random.uniform(40.0, 55.0)
            
            registers_to_write.extend([int(temp * 100), int(power * 100), int(hum * 100)])
            
        # Write out the entire massive layout register array block to address 0
        server.data_bank.set_holding_registers(0, registers_to_write)
        time.sleep(2)

except KeyboardInterrupt:
    server.stop()