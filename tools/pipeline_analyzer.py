#!/usr/bin/env python3
"""
Phase 2 — Pipeline Stage & ALU Structure Analysis

Traces data through the 3-stage pipeline (DBUS_0→DBUS_1→DBUS_2)
to identify ALU cells and reconstruct the data path.
"""

import json, sys, os
from collections import defaultdict, Counter

def analyze_pipeline(netlist_json):
    with open(netlist_json) as f:
        data = json.load(f)

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

    # Three pipeline stages
    stages = {
        'DBUS_0': '_07076_',
        'DBUS_1': '_07057_',
        'DBUS_2': '_07067_',
    }

    stage_cells = {}
    for label, bus in stages.items():
        cells = set()
        for i in range(8):
            w = f"{bus}[{i}]"
            for inst, pin, ct in wire_drivers.get(w, []):
                cells.add(inst)
            for inst, pin, ct in wire_readers.get(w, []):
                cells.add(inst)
        stage_cells[label] = cells
        print(f"{label} ({bus}): {len(cells)} cells ({len(wire_drivers.get(f'{bus}[0]',[]))} drivers)")

    # Find cells connected to BOTH DBUS_0 AND DBUS_1 (transition cells)
    s01 = stage_cells['DBUS_0'] & stage_cells['DBUS_1']
    s12 = stage_cells['DBUS_1'] & stage_cells['DBUS_2']
    s02 = stage_cells['DBUS_0'] & stage_cells['DBUS_2']
    print(f"\nPipeline overlap:")
    print(f"  DBUS_0 ∩ DBUS_1: {len(s01)} cells")
    print(f"  DBUS_1 ∩ DBUS_2: {len(s12)} cells")
    print(f"  DBUS_0 ∩ DBUS_2: {len(s02)} cells")

    # Find the "compute" cells: read from DBUS_1 (or DBUS_0) and write to DBUS_2
    # These are likely ALU cells
    compute_cells = set()
    for i in range(8):
        w1 = f"{stages['DBUS_1']}[{i}]"  # read from stage 1
        w2 = f"{stages['DBUS_2']}[{i}]"  # write to stage 2
        readers = set(inst for inst, _, _ in wire_readers.get(w1, []))
        drivers = set(inst for inst, _, _ in wire_drivers.get(w2, []))
        compute_cells |= (readers & drivers)

    print(f"\nCompute cells (read DBUS_1, write DBUS_2): {len(compute_cells)}")

    # What are the cell types in the compute layer?
    comp_types = Counter(cell_types.get(c, '?') for c in compute_cells)
    print(f"Compute cell types:")
    for ct, cnt in comp_types.most_common(15):
        print(f"  {ct}: {cnt}")

    # Also find CTRL bus readers in the compute layer
    ctrl_cells = set()
    for i in range(8):
        w = f"_07110_[{i}]"
        for inst, _, _ in wire_readers.get(w, []):
            ctrl_cells.add(inst)

    ctrl_in_compute = ctrl_cells & compute_cells
    print(f"\nCTRL bus readers in compute layer: {len(ctrl_in_compute)}")
    ctrl_types = Counter(cell_types.get(c, '?') for c in ctrl_in_compute)
    for ct, cnt in ctrl_types.most_common(5):
        print(f"  {ct}: {cnt}")

    # SFR → DBUS_0 → ALU → DBUS_1 → ALU → DBUS_2 → ACC
    # Trace SFR output to DBUS_0
    sfr_cells = set()
    for i in range(8):
        w = f"_07123_[{i}]"
        for inst, _, _ in wire_drivers.get(w, []):
            sfr_cells.add(inst)

    sfr_to_dbus0 = sfr_cells & stage_cells['DBUS_0']
    print(f"\nSFR→DBUS_0 cells: {len(sfr_to_dbus0)}")

    # ACC register cells → they write to DBUS_0
    acc_cells = set()
    for i in range(8):
        w = f"_07109_[{i}]"
        for inst, _, _ in wire_drivers.get(w, []):
            acc_cells.add(inst)
    print(f"ACC driver cells: {len(acc_cells)}")
    acc_types = Counter(cell_types.get(c, '?') for c in acc_cells)
    for ct, cnt in acc_types.most_common(5):
        print(f"  {ct}: {cnt}")

    return {
        'pipeline_stages': {k: len(v) for k, v in stage_cells.items()},
        'compute_cells': len(compute_cells),
        'compute_types': dict(comp_types.most_common(10)),
        'ctrl_in_compute': len(ctrl_in_compute),
    }


if __name__ == '__main__':
    nf = sys.argv[1] if len(sys.argv) > 1 else '../data/netlist_parsed.json'
    result = analyze_pipeline(nf)
    outdir = sys.argv[2] if len(sys.argv) > 2 else '../data'
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, 'pipeline_analysis.json'), 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved to {outdir}/pipeline_analysis.json")
