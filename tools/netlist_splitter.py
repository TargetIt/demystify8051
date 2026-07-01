#!/usr/bin/env python3
"""
Phase 4 — Netlist Module Splitter

Extracts functional modules from the flat gate-level netlist
by tracing bus-connected cells and their fan-in cones.
Outputs standalone Verilog submodules for formal equivalence checking.
"""

import json, sys, os, re
from collections import defaultdict

def load_netlist(json_path):
    with open(json_path) as f:
        return json.load(f)

def build_indices(data):
    wire_drivers = defaultdict(list)
    wire_readers = defaultdict(list)
    cell_by_inst = {}
    cell_conns = {}

    for cell in data['cells']:
        inst = cell['instance']
        cell_by_inst[inst] = cell
        cell_conns[inst] = cell['connections']
        for pin, wire in cell['connections'].items():
            if pin in ('Q','Y','X','CO','S','Z') or pin.startswith('Q'):
                wire_drivers[wire].append((inst, pin))
            else:
                wire_readers[wire].append((inst, pin))

    return wire_drivers, wire_readers, cell_by_inst, cell_conns

def trace_module_cells(start_buses, wire_readers, wire_drivers, cell_by_inst, max_depth=5):
    """Trace all cells connected to a set of characteristic buses."""
    module_cells = set()
    frontier = set()

    # Start from bus wires
    for bus_prefix in start_buses:
        for i in range(16):
            w = f"{bus_prefix}[{i}]"
            for inst, _ in wire_drivers.get(w, []):
                module_cells.add(inst)
                frontier.add(inst)
            for inst, _ in wire_readers.get(w, []):
                module_cells.add(inst)
                frontier.add(inst)

    # Expand by tracing fan-in/fan-out
    for _ in range(max_depth):
        new_frontier = set()
        for inst in list(frontier):
            conns = cell_by_inst[inst]['connections']
            for pin, wire in conns.items():
                for di, _ in wire_drivers.get(wire, []):
                    if di not in module_cells:
                        module_cells.add(di)
                        new_frontier.add(di)
                for ri, _ in wire_readers.get(wire, []):
                    if ri not in module_cells:
                        module_cells.add(ri)
                        new_frontier.add(ri)
        frontier = new_frontier
        if not frontier:
            break

    return module_cells

def extract_module_verilog(module_name, module_cells, data, wire_drivers, wire_readers):
    """Generate a standalone Verilog module for a set of cells."""
    # Collect all external interfaces
    external_inputs = set()
    external_outputs = set()
    internal_wires = set()

    for inst in module_cells:
        cell = data['cells'][data['cells'].index(next(c for c in data['cells'] if c['instance'] == inst))]
        for pin, wire in cell['connections'].items():
            # Check if wire driven from outside the module
            drivers = wire_drivers.get(wire, [])
            readers = wire_readers.get(wire, [])

            is_external_in = any(d[0] not in module_cells for d in drivers)
            is_external_out = any(r[0] not in module_cells for r in readers)

            if is_external_in:
                external_inputs.add(wire)
            if is_external_out:
                external_outputs.add(wire)
            if drivers or readers:
                internal_wires.add(wire)

    # Generate Verilog
    lines = []
    lines.append(f"// Auto-extracted submodule: {module_name}")
    lines.append(f"// Cells: {len(module_cells)}")
    lines.append("")
    lines.append(f"module {module_name} (")

    # Ports
    all_ports = sorted(external_inputs | external_outputs)
    port_wires = set()
    for p in all_ports:
        base = p.split('[')[0] if '[' in p else p
        if base not in port_wires:
            port_wires.add(base)
            # Check if it's a bus
            bus_wires = [w for w in all_ports if w.startswith(base)]
            if len(bus_wires) > 1:
                hi = max(int(w.split('[')[1].split(']')[0]) for w in bus_wires if '[' in w)
                lo = min(int(w.split('[')[1].split(']')[0]) for w in bus_wires if '[' in w)
                lines.append(f"    {'input' if base in external_inputs else 'output'} [{hi}:{lo}] {base},")
            else:
                direction = 'input' if p in external_inputs else 'output'
                lines.append(f"    {direction} {p},")
    lines[-1] = lines[-1].rstrip(',')  # remove trailing comma
    lines.append(");")

    # Wire declarations
    for w in sorted(internal_wires):
        if w not in all_ports:
            lines.append(f"  wire {w};")

    # Cell instantiations
    for inst in sorted(module_cells):
        cell = next(c for c in data['cells'] if c['instance'] == inst)
        lines.append(f"  {cell['cell_type']} {inst} (")
        pins = []
        for pin, wire in cell['connections'].items():
            pins.append(f"    .{pin}({wire})")
        lines.append(",\n".join(pins))
        lines.append("  );")

    lines.append("endmodule")
    return "\n".join(lines)

# ── Module definitions based on Phase 1-2 analysis ──
MODULE_BUSES = {
    'psw':      ['_07104_'],           # PSW flags[2:0]
    'alu':      ['_07109_', '_07121_', '_07076_', '_07057_', '_07067_'],
    'iram':     ['_07143_', '_07112_'],
    'sfr':      ['_07108_', '_07123_'],
    'decoder':  ['_07126_', '_07110_'],
    'timer':    ['_07154_', '_07155_', '_07156_', '_07157_', '_07188_', '_07189_'],
    'uart':     ['_07102_', '_07124_'],
    'intc':     ['_07230_', '_07138_'],
    'control':  ['_07110_'],
}

if __name__ == '__main__':
    infile = sys.argv[1] if len(sys.argv) > 1 else '../data/netlist_parsed.json'
    outdir = sys.argv[2] if len(sys.argv) > 2 else '../netlist_modules'

    data = load_netlist(infile)
    wire_drivers, wire_readers, cell_by_inst, cell_conns = build_indices(data)

    os.makedirs(outdir, exist_ok=True)

    all_module_cells = set()
    for mod_name, buses in MODULE_BUSES.items():
        cells = trace_module_cells(buses, wire_readers, wire_drivers, cell_by_inst)
        verilog = extract_module_verilog(mod_name, cells, data, wire_drivers, wire_readers)

        outpath = os.path.join(outdir, f"{mod_name}_gate.v")
        with open(outpath, 'w') as f:
            f.write(verilog)

        all_module_cells |= cells
        print(f"{mod_name}: {len(cells)} cells -> {outpath}")

    total = len(data['cells'])
    covered = len(all_module_cells)
    print(f"\nTotal coverage: {covered}/{total} cells ({covered/total*100:.1f}%)")
    print(f"Unassigned: {total - covered} cells")
