#!/usr/bin/env python3
"""
Phase 2 Batch B — Storage Module Analysis (IRAM + SFR Block)

Identifies storage arrays by tracing address/data bus connections
and classifying FFs by their connectivities.
"""

import json, sys, os
from collections import defaultdict, Counter

def analyze_storage(netlist_json, reg_map_json):
    with open(netlist_json) as f:
        data = json.load(f)
    with open(reg_map_json) as f:
        reg_info = json.load(f)

    wire_drivers = defaultdict(list)
    wire_readers = defaultdict(list)
    cell_conns = {}
    cell_types = {}

    for cell in data['cells']:
        inst = cell['instance']
        cell_types[inst] = cell['cell_type']
        conns = cell['connections']
        cell_conns[inst] = conns
        for pin, wire in conns.items():
            if pin in ('Q','Y','X','CO','S','Z') or pin.startswith('Q'):
                wire_drivers[wire].append((inst, pin, cell['cell_type']))
            else:
                wire_readers[wire].append((inst, pin, cell['cell_type']))

    # ── IRAM Analysis ──
    ram_addr_bus = '_07143_'
    ram_data_bus = '_07112_'

    # Cells connected to RAM address bus
    iram_cells = set()
    for i in range(8):
        w = f"{ram_addr_bus}[{i}]"
        for inst, _, _ in wire_drivers.get(w, []):
            iram_cells.add(inst)
        for inst, _, _ in wire_readers.get(w, []):
            iram_cells.add(inst)

    # Also include cells on data bus
    for i in range(3):
        w = f"{ram_data_bus}[{i}]"
        for inst, _, _ in wire_readers.get(w, []):
            iram_cells.add(inst)
        for inst, _, _ in wire_drivers.get(w, []):
            iram_cells.add(inst)

    print("=== IRAM Analysis ===")
    print(f"Cells on IRAM buses: {len(iram_cells)}")

    # IRAM FFs: FFs whose Q or D connects to IRAM cells via intermediate logic
    iram_ffs = set()
    for r in reg_info:
        inst = r['instance']
        q_wire = r.get('Q', '')
        d_wire = r.get('D', '')
        if q_wire:
            readers = {ri for ri, _, _ in wire_readers.get(q_wire, [])}
            if readers & iram_cells:
                iram_ffs.add(inst)
        if d_wire:
            drivers = {di for di, _, _ in wire_readers.get(d_wire, [])}  # cells that feed into D
            if drivers & iram_cells:
                iram_ffs.add(inst)

    print(f"IRAM FFs: {len(iram_ffs)}")

    # Cell types in IRAM
    iram_types = Counter(cell_types.get(c, '?') for c in iram_cells)
    print(f"IRAM cell types (top 10):")
    for ct, cnt in iram_types.most_common(10):
        print(f"  {ct}: {cnt}")

    # ── SFR Block Analysis ──
    sfr_din_bus = '_07108_'
    sfr_dout_bus = '_07123_'

    sfr_cells = set()
    for i in range(8):
        for bus in [sfr_din_bus, sfr_dout_bus]:
            w = f"{bus}[{i}]"
            for inst, _, _ in wire_drivers.get(w, []):
                sfr_cells.add(inst)
            for inst, _, _ in wire_readers.get(w, []):
                sfr_cells.add(inst)

    # Also: CTRL bus readers that also connect to SFR buses → SFR register selects
    ctrl_to_sfr = set()
    for i in range(8):
        w = f"_07110_[{i}]"
        for inst, _, _ in wire_readers.get(w, []):
            if inst in sfr_cells:
                ctrl_to_sfr.add(inst)

    print(f"\n=== SFR Block Analysis ===")
    print(f"Cells on SFR buses: {len(sfr_cells)}")
    print(f"CTRL readers in SFR area: {len(ctrl_to_sfr)}")

    # SFR FFs: likely dfrtp (with reset) on SFR buses
    sfr_ffs = set()
    for r in reg_info:
        inst = r['instance']
        ctype = r['cell_type']
        q_wire = r.get('Q', '')
        d_wire = r.get('D', '')
        if 'dfrtp' in ctype or 'dfstp' in ctype:  # has reset/set — typical for SFR
            if q_wire:
                readers = {ri for ri, _, _ in wire_readers.get(q_wire, [])}
                if readers & sfr_cells:
                    sfr_ffs.add(inst)
            elif d_wire:
                drv = {di for di, _, _ in wire_drivers.get(d_wire, [])}
                if drv & sfr_cells:
                    sfr_ffs.add(inst)

    all_sfr_ffs = set(r['instance'] for r in reg_info if 'dfrtp' in r['cell_type'] or 'dfstp' in r['cell_type'])
    print(f"Total dfrtp+dfstp (with reset/set): {len(all_sfr_ffs)}")
    print(f"SFR FFs (connected to SFR buses): {len(sfr_ffs)}")

    # Group SFR FFs by their Q-wire naming pattern (bus membership)
    sfr_ff_groups = defaultdict(list)
    for r in reg_info:
        q = r.get('Q', '')
        if q and '[' in q:
            base = q.split('[')[0]
            sfr_ff_groups[base].append(r)

    print(f"\nSFR register groups (by Q-wire bus):")
    for base, ffs in sorted(sfr_ff_groups.items(), key=lambda x: -len(x[1])):
        if len(ffs) >= 3:
            ctype_summary = Counter(r['cell_type'] for r in ffs)
            print(f"  {base}: {len(ffs)} FFs (types: {dict(ctype_summary)})")

    # ── Count remaining unclassified FFs ──
    used = iram_ffs | sfr_ffs | {r['instance'] for r in reg_info}
    all_ffs = {r['instance'] for r in reg_info}
    unclassified = all_ffs - used

    print(f"\n=== Summary ===")
    print(f"Total FFs: {len(all_ffs)}")
    print(f"IRAM FFs: {len(iram_ffs)}")
    print(f"SFR FFs (with reset): {len(sfr_ffs)}")
    print(f"Unclassified (data path/control): {len(unclassified)}")

    return {
        'iram': {'cells': len(iram_cells), 'ffs': len(iram_ffs)},
        'sfr': {'cells': len(sfr_cells), 'ffs': len(sfr_ffs), 'ctrl_connections': len(ctrl_to_sfr)},
        'unclassified': len(unclassified),
    }


if __name__ == '__main__':
    nf = sys.argv[1] if len(sys.argv) > 1 else '../data/netlist_parsed.json'
    rf = sys.argv[2] if len(sys.argv) > 2 else '../data/register_map.json'
    result = analyze_storage(nf, rf)
    outdir = sys.argv[3] if len(sys.argv) > 3 else '../data'
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, 'storage_analysis.json'), 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved to {outdir}/storage_analysis.json")
