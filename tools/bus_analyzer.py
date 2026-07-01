#!/usr/bin/env python3
"""
Phase 1 — Bus-Driven Module Boundary Analysis

Identifies module boundaries by analyzing which FFs connect to
which of the major identified buses. Each major functional module
in the 8051 has characteristic bus connections.
"""

import json, sys, os
from collections import defaultdict

def analyze_bus_ff_connections(netlist_json, reg_map_json):
    with open(netlist_json) as f:
        data = json.load(f)
    with open(reg_map_json) as f:
        reg_info = json.load(f)

    # Build indices
    wire_drivers = defaultdict(list)
    wire_readers = defaultdict(list)
    cell_conns = {}

    for cell in data['cells']:
        inst = cell['instance']
        cell_conns[inst] = cell['connections']
        for pin, wire in cell['connections'].items():
            if pin in ('Q','Y','X','CO','S','Z') or pin.startswith('Q'):
                wire_drivers[wire].append((inst, pin, cell['cell_type']))
            else:
                wire_readers[wire].append((inst, pin, cell['cell_type']))

    # Key buses identified in P1.3
    key_buses = [
        ('IR', '_07126_', 7, 'Instruction Register'),
        ('PC', '_07111_', 16, 'Program Counter'),
        ('ACC', '_07109_', 8, 'Accumulator / Data Bus A'),
        ('DB_B', '_07121_', 8, 'Data Bus B / ALU Input B'),
        ('CTRL', '_07110_', 8, 'Control Signals'),
        ('PSW_FLAGS', '_07104_', 3, 'PSW Flags (CY, AC, OV)'),
        ('ADDR', '_07127_', 12, 'Address Bus'),
        ('DBUS_0', '_07076_', 8, 'Data Bus Stage 0'),
        ('DBUS_1', '_07057_', 8, 'Data Bus Stage 1'),
        ('DBUS_2', '_07067_', 8, 'Data Bus Stage 2'),
        ('SFR_DIN', '_07108_', 8, 'SFR Data Input'),
        ('SFR_DOUT', '_07123_', 8, 'SFR Data Output'),
        ('RAM_ADDR', '_07143_', 8, 'RAM Address'),
        ('RAM_DATA', '_07112_', 3, 'RAM Data/Control'),
        ('PC_LOW', '_07106_', 8, 'PC Low Byte'),
    ]

    # Map each FF to the buses it connects to (as driver or reader)
    ff_to_buses = defaultdict(set)
    for r in reg_info:
        inst = r['instance']
        conns = cell_conns.get(inst, {})
        all_wires = set(conns.values())
        for bus_label, bus_name, width, desc in key_buses:
            for i in range(width):
                bit_name = f"{bus_name}[{i}]"
                if bit_name in all_wires:
                    ff_to_buses[inst].add(bus_label)

    # Group FFs by their bus signature
    bus_groups = defaultdict(list)
    for inst, buses in ff_to_buses.items():
        key = tuple(sorted(buses))
        bus_groups[key].append(inst)

    # Sort groups by size
    sorted_groups = sorted(bus_groups.items(), key=lambda x: -len(x[1]))

    return {
        'bus_labels': {b[0]: {'bus': b[1], 'width': b[2], 'desc': b[3]} for b in key_buses},
        'ff_bus_groups': [
            {'buses': list(k), 'ff_count': len(v), 'samples': v[:5]}
            for k, v in sorted_groups[:30]
        ],
        'total_grouped': sum(len(v) for v in bus_groups.values()),
        'num_groups': len(bus_groups),
    }


if __name__ == '__main__':
    netfile = sys.argv[1] if len(sys.argv) > 1 else '../data/netlist_parsed.json'
    regfile = sys.argv[2] if len(sys.argv) > 2 else '../data/register_map.json'
    outfile = sys.argv[3] if len(sys.argv) > 3 else '../data/bus_analysis.json'

    result = analyze_bus_ff_connections(netfile, regfile)

    print("=== Bus-Driven FF Groups ===")
    print(f"Total FFs grouped by bus connectivity: {result['total_grouped']}")
    print(f"Number of unique bus signatures: {result['num_groups']}")
    print(f"\nTop 20 bus signatures:")
    for g in result['ff_bus_groups'][:20]:
        buses = ', '.join(g['buses'])
        print(f"  [{buses}]: {g['ff_count']} FFs (e.g. {g['samples'][:3]})")

    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    with open(outfile, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved to {outfile}")
