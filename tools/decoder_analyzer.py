#!/usr/bin/env python3
"""
Phase 2 — Decoder & ALU Reverse Engineering

Analyzes the instruction register (IR) bus fanout to reconstruct:
  1. Decoder: IR bits → control signal mapping (microcode reconstitution)
  2. ALU: data path and operation control signals

Method:
  For each IR bit, trace its fanout through combinational logic
  to identify what control signals are generated at each opcode value.
"""

import json, sys, os
from collections import defaultdict, Counter

class DecoderAnalyzer:
    def __init__(self, netlist_json, reg_json, bus_json):
        with open(netlist_json) as f:
            self.data = json.load(f)
        with open(reg_json) as f:
            self.reg_info = json.load(f)
        with open(bus_json) as f:
            self.bus_info = json.load(f)

        self.cells = self.data['cells']
        self._build_indices()

    def _build_indices(self):
        self.wire_drivers = defaultdict(list)
        self.wire_readers = defaultdict(list)
        self.cell_conns = {}
        self.cell_types = {}

        for cell in self.cells:
            inst = cell['instance']
            ctype = cell['cell_type']
            self.cell_types[inst] = ctype
            conns = cell['connections']
            self.cell_conns[inst] = conns
            for pin, wire in conns.items():
                if pin in ('Q','Y','X','CO','S','Z') or pin.startswith('Q'):
                    self.wire_drivers[wire].append((inst, pin, ctype))
                else:
                    self.wire_readers[wire].append((inst, pin, ctype))

    def analyze_ir(self):
        """Trace IR bus (_07126_) fanout — decode logic reconstruction."""
        ir_wires = [f"_07126_[{i}]" for i in range(7)]

        # Level 1: direct readers of IR bits
        l1_readers = defaultdict(list)
        for i, w in enumerate(ir_wires):
            for inst, pin, ctype in self.wire_readers.get(w, []):
                l1_readers[inst].append(('ir', i, pin))

        print(f"Level 1 IR readers: {len(l1_readers)} unique cells")
        print(f"  Total reader instances: {sum(len(v) for v in l1_readers.values())}")

        # Level 2: what do L1 cells drive? (control signal generation)
        l2_signals = defaultdict(list)
        for inst in l1_readers:
            for pin, wire in self.cell_conns.get(inst, {}).items():
                if pin in ('Q','Y','X','Z') or pin.startswith('Q'):
                    readers = self.wire_readers.get(wire, [])
                    for ri, rp, rc in readers:
                        l2_signals[wire].append({
                            'driver': inst,
                            'driver_type': self.cell_types.get(inst, '?'),
                            'target': ri,
                            'target_type': rc
                        })

        # Count how many L2 wires are buses
        top_signals = sorted(l2_signals.items(), key=lambda x: -len(x[1]))
        print(f"\nLevel 2 control signals (from IR decoder): {len(l2_signals)}")
        print("Top 20 by fanout:")
        for wire, targets in top_signals[:20]:
            print(f"  {wire}: {len(targets)} targets (driver: {targets[0]['driver']} [{targets[0]['driver_type']}])")

        # Count cell types involved in decoder
        l1_types = Counter(self.cell_types.get(inst, '?') for inst in l1_readers)
        print(f"\nDecoder cell type distribution:")
        for ct, cnt in l1_types.most_common(15):
            print(f"  {ct}: {cnt}")

        return {
            'l1_reader_count': len(l1_readers),
            'l2_signal_count': len(l2_signals),
            'top_l2_signals': [(w, len(t)) for w, t in top_signals[:30]],
            'cell_types': dict(l1_types),
        }

    def analyze_data_path(self):
        """Trace key data path buses to understand pipeline stages."""
        key_buses = {
            'ACC': '_07109_',
            'DB_B': '_07121_',
            'PC': '_07111_',
            'DBUS_0': '_07076_',
            'DBUS_1': '_07057_',
            'DBUS_2': '_07067_',
            'SFR_DOUT': '_07123_',
            'SFR_DIN': '_07108_',
            'IR': '_07126_',
            'CTRL': '_07110_',
        }

        result = {}
        for label, bus in key_buses.items():
            drivers = set()
            readers = set()
            for i in range(16):  # max width
                w = f"{bus}[{i}]"
                for inst, pin, ct in self.wire_drivers.get(w, []):
                    drivers.add((inst, ct))
                for inst, pin, ct in self.wire_readers.get(w, []):
                    readers.add((inst, ct))
                if i >= 7 and not self.wire_drivers.get(w) and not self.wire_readers.get(w):
                    break  # bus is narrower than 16

            result[label] = {
                'bus': bus,
                'driver_count': len(drivers),
                'reader_count': len(readers),
                'driver_types': Counter(ct for _, ct in drivers).most_common(5),
            }

        print("\n=== Data Path Bus Summary ===")
        for label, info in result.items():
            print(f"  {label} ({info['bus']}): {info['driver_count']} drivers, {info['reader_count']} readers")

        return result

    def analyze_alu_inputs(self):
        """Identify ALU operation by analyzing ACC and DB_B data paths."""
        acc_bus = '_07109_'
        dbb_bus = '_07121_'
        ctrl_bus = '_07110_'

        # Find cells that read from BOTH ACC and DB_B — these are ALU cells
        acc_readers = set()
        dbb_readers = set()
        for i in range(8):
            for inst, _, _ in self.wire_readers.get(f"{acc_bus}[{i}]", []):
                acc_readers.add(inst)
            for inst, _, _ in self.wire_readers.get(f"{dbb_bus}[{i}]", []):
                dbb_readers.add(inst)

        alu_cells = acc_readers & dbb_readers
        print(f"\n=== ALU Cell Analysis ===")
        print(f"ACC readers: {len(acc_readers)}, DB_B readers: {len(dbb_readers)}")
        print(f"Intersection (likely ALU cells): {len(alu_cells)}")

        # What cell types are used in ALU?
        alu_types = Counter(self.cell_types.get(c, '?') for c in alu_cells)
        print(f"ALU cell types:")
        for ct, cnt in alu_types.most_common(10):
            print(f"  {ct}: {cnt}")

        # CTRL bus wires might select ALU op
        ctrl_fanout = {}
        for i in range(8):
            w = f"{ctrl_bus}[{i}]"
            readers = self.wire_readers.get(w, [])
            # Which of those readers are ALU cells?
            alu_hits = [r for r in readers if r[0] in alu_cells]
            if alu_hits:
                ctrl_fanout[i] = len(alu_hits)

        print(f"\nCTRL bits reaching ALU: {ctrl_fanout}")

        return {
            'acc_readers': len(acc_readers),
            'dbb_readers': len(dbb_readers),
            'alu_cells': len(alu_cells),
            'alu_cell_types': dict(alu_types.most_common(10)),
            'ctrl_to_alu': ctrl_fanout,
        }


if __name__ == '__main__':
    netfile = sys.argv[1] if len(sys.argv) > 1 else '../data/netlist_parsed.json'
    regfile = sys.argv[2] if len(sys.argv) > 2 else '../data/register_map.json'
    busfile = sys.argv[3] if len(sys.argv) > 3 else '../data/bus_analysis.json'
    outdir = sys.argv[4] if len(sys.argv) > 4 else '../data'

    a = DecoderAnalyzer(netfile, regfile, busfile)

    ir_result = a.analyze_ir()
    dp_result = a.analyze_data_path()
    alu_result = a.analyze_alu_inputs()

    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, 'decoder_analysis.json'), 'w') as f:
        json.dump({'ir_decoder': ir_result, 'data_path': dp_result, 'alu': alu_result}, f, indent=2)
    print(f"\nSaved to {outdir}/decoder_analysis.json")
