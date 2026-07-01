#!/usr/bin/env python3
"""
Smart Netlist Splitter — assigns cells to modules by bus ownership,
then extracts gate-level submodules for formal equivalence.
"""

import json, sys, os
from collections import defaultdict

# ── Module definitions: (input_buses, output_buses, name) ──
MODULES = {
    'alu': {
        'inputs':  ['_07109_', '_07121_'],           # ACC, DB_B (B reg)
        'outputs': ['_07076_', '_07057_', '_07067_'], # DBUS_0, DBUS_1, DBUS_2
        'control': ['_07110_'],                       # CTRL (op select)
    },
    'decoder': {
        'inputs':  ['_07126_'],                       # IR
        'outputs': ['_07110_'],                       # CTRL
    },
    'psw': {
        'inputs':  ['_07057_', '_07110_'],            # ALU flags input
        'outputs': ['_07104_'],                       # PSW flags
    },
    'iram': {
        'inputs':  ['_07143_'],                       # RAM_ADDR
        'outputs': ['_07112_'],                       # RAM_DATA
    },
    'sfr': {
        'inputs':  ['_07127_', '_07110_'],            # ADDR, CTRL
        'outputs': ['_07108_', '_07123_'],            # SFR_DIN, SFR_DOUT
    },
    'timer': {
        'inputs':  ['_07188_', '_07189_'],            # TCON, TMOD
        'outputs': ['_07154_', '_07155_', '_07156_', '_07157_'],  # TL0, TL1, TH0, TH1
    },
    'uart': {
        'inputs':  ['_07102_'],                       # SCON
        'outputs': ['_07124_'],                       # SBUF
    },
    'intc': {
        'inputs':  ['_07230_', '_07138_'],            # IE, IP
        'outputs': [],                                # internal control
    },
}

def load_data(json_path):
    with open(json_path) as f:
        return json.load(f)

def build_indices(data):
    wire_drivers = defaultdict(list)  # wire -> [(inst, pin), ...]
    wire_readers = defaultdict(list)  # wire -> [(inst, pin), ...]
    cell_conns = {}
    for cell in data['cells']:
        inst = cell['instance']
        cell_conns[inst] = cell['connections']
        for pin, wire in cell['connections'].items():
            if pin in ('Q','Y','X','CO','S','Z') or pin.startswith('Q'):
                wire_drivers[wire].append(inst)
            else:
                wire_readers[wire].append(inst)
    return wire_drivers, wire_readers, cell_conns

def expand_bus(bus, wire_readers, wire_drivers):
    """Expand bus prefix to actual wire names"""
    wires = set()
    for i in range(32):
        w = f"{bus}[{i}]"
        if w in wire_drivers or w in wire_readers:
            wires.add(w)
        else:
            break
    return wires

def extract_module_cells(mod_name, mod_def, wire_drivers, wire_readers, cell_conns, data):
    """Extract cells belonging to a module by tracing from its I/O buses"""
    module_cells = set()
    module_wires = set()

    # Collect all bus wires for this module
    input_wires = set()
    output_wires = set()
    control_wires = set()

    for bus in mod_def.get('inputs', []):
        input_wires |= expand_bus(bus, wire_readers, wire_drivers)
    for bus in mod_def.get('outputs', []):
        output_wires |= expand_bus(bus, wire_readers, wire_drivers)
        input_wires |= output_wires  # outputs are also part of module internal wires
    for bus in mod_def.get('control', []):
        control_wires |= expand_bus(bus, wire_readers, wire_drivers)

    all_module_wires = input_wires | output_wires | control_wires

    # Pass 1: cells that drive module output wires BELONG to this module
    for w in output_wires:
        for inst in wire_drivers.get(w, []):
            module_cells.add(inst)

    # Pass 2: cells that these drivers read from ALSO belong (fan-in)
    for _ in range(2):  # 2 levels of fan-in
        new_cells = set()
        for inst in list(module_cells):
            for pin, wire in cell_conns[inst].items():
                if pin not in ('Q','Y','X','CO','S','Z') and not pin.startswith('Q'):
                    for driver in wire_drivers.get(wire, []):
                        if driver not in module_cells:
                            new_cells.add(driver)
        module_cells |= new_cells

    # Pass 3: cells that read module input wires and feed into module cells
    for w in input_wires | control_wires:
        readers = wire_readers.get(w, [])
        for inst in readers:
            # Check if this reader connects to other module cells
            conns = cell_conns.get(inst, {})
            is_connected_to_module = False
            for pin, wire in conns.items():
                if pin in ('Q','Y','X','CO','S','Z') or pin.startswith('Q'):
                    if any(r in module_cells for r in wire_readers.get(wire, [])):
                        is_connected_to_module = True
                        break
            if is_connected_to_module:
                module_cells.add(inst)

    return module_cells

def group_bus_wires(wires):
    """Group individual _name_[n] wires into buses."""
    singles = set()
    buses = defaultdict(set)
    for w in wires:
        if '[' in w:
            base = w.split('[')[0]
            idx = int(w.split('[')[1].split(']')[0])
            buses[base].add(idx)
        else:
            singles.add(w)
    return singles, dict(buses)

def wire_decl(name, direction, buses, singles):
    """Generate port declaration for bus or single wire."""
    if name in buses:
        idxs = buses[name]
        hi, lo = max(idxs), min(idxs)
        if hi == lo:
            return f"    {direction} {name}[{hi}]"
        return f"    {direction} [{hi}:{lo}] {name}"
    elif name in singles:
        return f"    {direction} {name}"
    return None

def write_module_verilog(mod_name, module_cells, data, wire_drivers, wire_readers, cell_conns):
    """Write extracted cells as a standalone Verilog module"""
    internal_wires = set()
    external_inputs = set()
    external_outputs = set()

    for inst in module_cells:
        conns = cell_conns[inst]
        for pin, wire in conns.items():
            internal_wires.add(wire)
            is_output_pin = pin in ('Q','Y','X','CO','S','Z') or pin.startswith('Q')
            if is_output_pin:
                readers = wire_readers.get(wire, [])
                if any(r not in module_cells for r in readers):
                    external_outputs.add(wire)
            else:
                drivers = wire_drivers.get(wire, [])
                if all(d not in module_cells for d in drivers):
                    external_inputs.add(wire)

    # Group into buses
    in_singles, in_buses = group_bus_wires(external_inputs)
    out_singles, out_buses = group_bus_wires(external_outputs)
    int_singles, int_buses = group_bus_wires(internal_wires)

    all_input_names = set(in_singles) | set(in_buses.keys())
    all_output_names = set(out_singles) | set(out_buses.keys())
    all_int_names = set(int_singles) | set(int_buses.keys())
    all_ext_names = all_input_names | all_output_names

    lines = [f"// Auto-extracted: {mod_name} ({len(module_cells)} cells)"]
    lines.append(f"module {mod_name}_gate (")

    # Port declarations with bus grouping
    for name in sorted(all_input_names):
        decl = wire_decl(name, 'input', in_buses, in_singles)
        if decl: lines.append(decl + ",")
    for name in sorted(all_output_names - all_input_names):
        decl = wire_decl(name, 'output', out_buses, out_singles)
        if decl: lines.append(decl + ",")

    # clk/rst
    has_seq = any('df' in data['cells'][i]['cell_type'] for i in range(len(data['cells']))
                   if data['cells'][i]['instance'] in module_cells)
    # Only add clk/rst if not already in port list
    if 'clk' not in all_ext_names:
        lines.append("    input clk,")
    if 'rst_n' not in all_ext_names:
        lines.append("    input rst_n")
    lines.append(");")

    # Internal wire declarations
    for name in sorted(all_int_names - all_ext_names):
        decl = wire_decl(name, 'wire', int_buses, int_singles)
        if decl: lines.append(decl.replace('    wire', '  wire') + ";")

    # Cell instantiations
    for inst in sorted(module_cells):
        cell = next(c for c in data['cells'] if c['instance'] == inst)
        pins = [f"    .{pin}({wire})" for pin, wire in cell['connections'].items()]
        lines.append(f"  {cell['cell_type']} {inst} (")
        lines.append(",\n".join(pins))
        lines.append("  );")

    lines.append("endmodule")
    return "\n".join(lines)


if __name__ == '__main__':
    infile = sys.argv[1] if len(sys.argv) > 1 else '../data/netlist_parsed.json'
    outdir = sys.argv[2] if len(sys.argv) > 2 else '../gate_modules'

    data = load_data(infile)
    wire_drivers, wire_readers, cell_conns = build_indices(data)
    os.makedirs(outdir, exist_ok=True)

    total = 0
    for mod_name, mod_def in MODULES.items():
        cells = extract_module_cells(mod_name, mod_def, wire_drivers, wire_readers, cell_conns, data)
        if cells:
            verilog = write_module_verilog(mod_name, cells, data, wire_drivers, wire_readers, cell_conns)
            outpath = os.path.join(outdir, f"{mod_name}_gate.v")
            with open(outpath, 'w') as f:
                f.write(verilog)
            total += len(cells)
            print(f"{mod_name}: {len(cells)} cells -> {outpath}")

    print(f"\nTotal extracted: {total}/{len(data['cells'])} cells ({total/len(data['cells'])*100:.1f}%)")
