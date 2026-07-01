#!/usr/bin/env python3
"""
Phase 0.1 — Verilog Flat Netlist Parser

Parses a Yosys-generated flat gate-level netlist into Python data structures.
Input: echo_8051_synth.v (flat, single module, Sky130 HD cells)
Output: JSON with metadata, cell list, wire list, port list
"""

import re, json, sys
from collections import defaultdict

def parse_netlist(filepath):
    with open(filepath, 'r') as f:
        text = f.read()

    result = {
        'module_name': None,
        'ports': [],
        'wires': [],
        'cells': [],
        'stats': {}
    }

    # Extract module header
    m = re.search(r'module\s+(\w+)\s*\(([^)]+)\)', text)
    if m:
        result['module_name'] = m.group(1)
        ports_raw = [p.strip() for p in m.group(2).split(',')]
    else:
        raise ValueError("No module declaration found")

    # Parse port declarations (input/output/inout)
    port_decls = defaultdict(list)
    for decl in re.finditer(r'(input|output|inout)\s+(?:\[\d+:\d+\]\s+)?(\w+)', text):
        port_decls[decl.group(2)].append(decl.group(1))

    for pname in ports_raw:
        result['ports'].append({
            'name': pname,
            'direction': port_decls.get(pname, ['unknown'])[0]
        })

    # Parse wire declarations (single-bit and bus)
    wire_single = set()
    wire_bus = {}

    # Bus wires: wire [7:0] _00000_;
    for m in re.finditer(r'wire\s+\[(\d+):(\d+)\]\s+(\w+)', text):
        hi, lo, name = int(m.group(1)), int(m.group(2)), m.group(3)
        wire_bus[name] = {'hi': hi, 'lo': lo, 'width': hi-lo+1}

    # Single-bit wires: wire _XXXXX_;
    for m in re.finditer(r'wire\s+(\w+)\s*;', text):
        wname = m.group(1)
        if wname not in wire_bus and wname not in ports_raw:
            wire_single.add(wname)

    result['wires'] = {
        'single_bit': sorted(wire_single),
        'bus': {k: v for k, v in sorted(wire_bus.items())},
        'single_count': len(wire_single),
        'bus_count': len(wire_bus)
    }

    # Parse cell instances (multi-line: type inst ( .PIN(wire), ... ); )
    cell_types = defaultdict(int)
    cells = []

    cell_re = re.compile(r'(sky130_fd_sc_hd__\w+)\s+(\w+)\s*\((.*?)\)\s*;', re.DOTALL)
    for m in cell_re.finditer(text):
        cell_type = m.group(1)
        inst_name = m.group(2)
        pins_raw = m.group(3)

        cell_types[cell_type] += 1

        # Parse pin connections: .PIN(wire) or .PIN(wire[msb:lsb])
        connections = {}
        for pm in re.finditer(r'\.(\w+)\s*\(\s*(\w+(?:\[\d+(?::\d+)?\])?)\s*\)', pins_raw):
            pin_name = pm.group(1)
            wire_name = pm.group(2)
            connections[pin_name] = wire_name

        cells.append({
            'instance': inst_name,
            'cell_type': cell_type,
            'connections': connections
        })

    result['cells'] = cells
    result['stats'] = {
        'total_cells': len(cells),
        'unique_cell_types': len(cell_types),
        'cell_type_breakdown': sorted(cell_types.items(), key=lambda x: -x[1]),
        'wire_single_count': len(wire_single),
        'wire_bus_count': len(wire_bus),
        'port_count': len(result['ports'])
    }

    return result


if __name__ == '__main__':
    filepath = sys.argv[1] if len(sys.argv) > 1 else '../input/echo_8051_synth.v'
    result = parse_netlist(filepath)

    # Stats
    stats = result['stats']
    print(f"Module: {result['module_name']}")
    print(f"Ports: {stats['port_count']}")
    print(f"Cells: {stats['total_cells']}")
    print(f"Cell types: {stats['unique_cell_types']}")
    print(f"Wires (single): {stats['wire_single_count']}")
    print(f"Wires (bus): {stats['wire_bus_count']}")

    # DFF count
    dff_types = ['dfrtp', 'dfstp', 'dfxtp']
    dff_count = sum(v for k, v in result['stats']['cell_type_breakdown'] if any(d in k for d in dff_types))
    print(f"Flip-flops: {dff_count}")

    # Top cell types
    print("\nTop 10 cell types:")
    for ct, cnt in result['stats']['cell_type_breakdown'][:10]:
        print(f"  {ct}: {cnt}")

    # Save
    outpath = sys.argv[2] if len(sys.argv) > 2 else '../data/netlist_parsed.json'
    import os
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nSaved to {outpath}")
