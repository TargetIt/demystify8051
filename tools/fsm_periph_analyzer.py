#!/usr/bin/env python3
"""
Phase 2 Batch C+D — Control FSM & Peripheral Analysis

Identifies remaining control and peripheral logic by tracing
control signal paths and specialized counter/shifter structures.
"""

import json, sys, os
from collections import defaultdict, Counter

def analyze_fsm_periph(netlist_json, reg_json):
    with open(netlist_json) as f:
        data = json.load(f)
    with open(reg_json) as f:
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

    # Classify previously-unclassified FFs into functional modules
    # We've already assigned: IRAM (51), SFR (~184), ALU/DataPath (~121 from Phase 1)
    # Remaining ~1,270 FFs should be: Control FSM states, pipeline registers, temp storage

    # ── Control FSM: FFs connected to CTRL bus ──
    ctrl_bus = '_07110_'
    ctrl_ffs = set()
    for i in range(8):
        w = f"{ctrl_bus}[{i}]"
        for inst, _, ct in wire_drivers.get(w, []):
            ctrl_ffs.add(inst)

    ctrl_state_ffs = [r for r in reg_info if r['instance'] in ctrl_ffs]
    print(f"=== Control FSM Analysis ===")
    print(f"CTRL bus FFs: {len(ctrl_ffs)}")
    print(f"CTRL FF types: {Counter(r['cell_type'] for r in ctrl_state_ffs).most_common()}")

    # Control FSM likely has a few state FFs + lots of decoded signal drivers
    # State FFs are typically dfrtp (control state needs reset)
    ctrl_state_types = Counter(r['cell_type'] for r in ctrl_state_ffs)
    state_ff_count = ctrl_state_types.get('sky130_fd_sc_hd__dfrtp_1', 0)
    print(f"  State FFs (dfrtp): {state_ff_count}")
    print(f"  Pipeline FFs (dfxtp): {ctrl_state_types.get('sky130_fd_sc_hd__dfxtp_1', 0)}")

    # FSM likely has 4-8 main states (FETCH, DECODE, EXEC1, EXEC2, WRITEBACK)
    # With ~8 state FFs encoding the FSM

    # ── Timer: T0/T1 counter FFs ──
    timer_sfr = ['_07154_', '_07155_', '_07156_', '_07157_']  # TL0, TL1, TH0, TH1
    timer_ffs = set()
    for bus in timer_sfr:
        for i in range(8):
            w = f"{bus}[{i}]"
            for inst, _, _ in wire_drivers.get(w, []):
                timer_ffs.add(inst)
            for inst, _, _ in wire_readers.get(w, []):
                timer_ffs.add(inst)

    print(f"\n=== Timer (T0/T1) Analysis ===")
    print(f"Timer SFR cells: {len(timer_ffs)}")

    # Timer control: TCON _07188_ + TMOD _07189_
    tcon_cells = set()
    for i in range(8):
        w = f"_07188_[{i}]"
        for inst, _, _ in wire_readers.get(w, []):
            tcon_cells.add(inst)
    print(f"TCON (_07188_) readers: {len(tcon_cells)}")

    # Timer overflow detection: look for COUNTER FF patterns
    # A counter is a chain of xor + carry cells
    timer_control_types = Counter(cell_types.get(c, '?') for c in timer_ffs)
    print(f"Timer cell types (top 5):")
    for ct, cnt in timer_control_types.most_common(5):
        print(f"  {ct}: {cnt}")

    # ── UART Analysis ──
    uart_sfr = ['_07102_', '_07124_']  # SCON, SBUF
    uart_cells = set()
    for bus in uart_sfr:
        for i in range(8):
            w = f"{bus}[{i}]"
            for inst, _, _ in wire_readers.get(w, []):
                uart_cells.add(inst)
            for inst, _, _ in wire_drivers.get(w, []):
                uart_cells.add(inst)

    # Also trace rxd/txd pins into UART area
    for pin in ['rxd', 'txd']:
        for inst, _, _ in wire_readers.get(pin, []):
            uart_cells.add(inst)
        for inst, _, _ in wire_drivers.get(pin, []):
            uart_cells.add(inst)

    print(f"\n=== UART Analysis ===")
    print(f"UART cells: {len(uart_cells)}")
    uart_types = Counter(cell_types.get(c, '?') for c in uart_cells)
    print(f"UART cell types (top 5):")
    for ct, cnt in uart_types.most_common(5):
        print(f"  {ct}: {cnt}")

    # ── Interrupt Controller ──
    intc_sfr = ['_07230_', '_07138_']  # IE, IP
    intc_cells = set()
    for bus in intc_sfr:
        for i in range(8):
            w = f"{bus}[{i}]"
            for inst, _, _ in wire_readers.get(w, []):
                intc_cells.add(inst)

    for pin in ['int0_n', 'int1_n']:
        for inst, _, _ in wire_readers.get(pin, []):
            intc_cells.add(inst)

    print(f"\n=== Interrupt Controller Analysis ===")
    print(f"IntC cells: {len(intc_cells)}")
    intc_types = Counter(cell_types.get(c, '?') for c in intc_cells)
    for ct, cnt in intc_types.most_common(5):
        print(f"  {ct}: {cnt}")

    # ── Summary: map all major FFs to modules ──
    all_ffs = {r['instance']: r for r in reg_info}
    assigned = set()

    # Count by bus group
    module_map = {
        'Decoder (IR)': '_07126_',
        'ACC': '_07109_', 'B': '_07121_', 'ALU (XOR/XNOR)': '',
        'PC': '_07111_', 'CTRL': '_07110_',
        'PSW': '_07104_',
        'DataPath (DBUS_0)': '_07076_', 'DataPath (DBUS_1)': '_07057_', 'DataPath (DBUS_2)': '_07067_',
        'SFR_DIN': '_07108_', 'SFR_DOUT': '_07123_',
        'IRAM_ADDR': '_07143_', 'IRAM_DATA': '_07112_',
        'Timer (TCON)': '_07188_', 'Timer (TMOD)': '_07189_', 'Timer (TL0)': '_07154_',
        'Timer (TL1)': '_07155_', 'Timer (TH0)': '_07156_', 'Timer (TH1)': '_07157_',
        'UART (SCON)': '_07102_', 'UART (SBUF)': '_07124_',
        'IntC (IE)': '_07230_', 'IntC (IP)': '_07138_',
    }

    module_ff_counts = defaultdict(int)
    for mod_name, bus in module_map.items():
        if not bus: continue
        for i in range(16):
            w = f"{bus}[{i}]"
            for inst, _, _ in wire_drivers.get(w, []):
                if inst in all_ffs:
                    assigned.add(inst)
                    module_ff_counts[mod_name.split('(')[0].strip()] += 1

    # Count IRAM FFs
    iram_range = range(0x6895, 0x7055)  # _06895_ to _07054_
    iram_count = sum(1 for r in reg_info if r['instance'] > '_06894_' and r['instance'] < '_07055_')

    print(f"\n=== Module FF Distribution ===")
    for mod, cnt in sorted(module_ff_counts.items(), key=lambda x: -x[1]):
        print(f"  {mod}: {cnt} FFs")
    print(f"  IRAM: ~{iram_count} FFs (128×8 array)")
    print(f"  Total assigned: {sum(module_ff_counts.values()) + iram_count}")
    print(f"  Remaining (internal pipeline/temp): {len(all_ffs) - len(assigned) - iram_count}")

    return {
        'control_fsm': {'ctrl_ffs': len(ctrl_ffs), 'state_ffs': state_ff_count},
        'timer': {'cells': len(timer_ffs), 'tcon_readers': len(tcon_cells)},
        'uart': {'cells': len(uart_cells)},
        'intc': {'cells': len(intc_cells)},
        'module_ffs': dict(module_ff_counts),
    }


if __name__ == '__main__':
    nf = sys.argv[1] if len(sys.argv) > 1 else '../data/netlist_parsed.json'
    rf = sys.argv[2] if len(sys.argv) > 2 else '../data/register_map.json'
    result = analyze_fsm_periph(nf, rf)
    outdir = sys.argv[3] if len(sys.argv) > 3 else '../data'
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, 'fsm_periph_analysis.json'), 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved to {outdir}/fsm_periph_analysis.json")
