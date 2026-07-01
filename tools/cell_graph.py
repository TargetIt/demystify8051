#!/usr/bin/env python3
"""
Phase 0.2 — Cell Graph Builder

Builds a directed graph from the parsed netlist (Phase 0.1 output).
Provides efficient queries:
  - fanin(cell) / fanout(cell)
  - Register identification and grouping
  - Wire-driven and pin-driven traversal
"""

import json, sys, os
from collections import defaultdict

class CellGraph:
    def __init__(self, netlist_data):
        self.data = netlist_data
        self._build_indices()

    def _build_indices(self):
        """Build fast lookup structures."""
        # wire -> list of (cell_instance, pin_name) that drive this wire
        self.wire_drivers = defaultdict(list)
        # wire -> list of (cell_instance, pin_name) that read this wire
        self.wire_readers = defaultdict(list)
        # cell_instance -> {pin_name: wire_name}
        self.cell_connections = {}
        # cell_instance -> cell_type
        self.cell_types = {}
        # wire name -> bus base name (if part of bus)
        self.wire_to_bus = {}

        # Populate from parsed data
        for cell in self.data['cells']:
            inst = cell['instance']
            ctype = cell['cell_type']
            self.cell_types[inst] = ctype
            conns = cell['connections']
            self.cell_connections[inst] = conns

            for pin, wire in conns.items():
                driver_pins = {'Q', 'Y', 'X', 'CO', 'S', 'Z'}
                if pin in driver_pins or pin.startswith('Q'):
                    self.wire_drivers[wire].append((inst, pin))
                else:
                    self.wire_readers[wire].append((inst, pin))

        # Build bus index: _00000_[0] -> _00000_
        for bus_name, info in self.data['wires']['bus'].items():
            for i in range(info['lo'], info['hi'] + 1):
                bit_name = f"{bus_name}[{i}]"
                self.wire_to_bus[bit_name] = bus_name

    def fanout(self, cell_instance):
        """Return list of (wire, target_cells) that this cell drives."""
        result = []
        conns = self.cell_connections.get(cell_instance, {})
        for pin, wire in conns.items():
            driver_pins = {'Q', 'Y', 'X', 'CO', 'S', 'Z'}
            if pin in driver_pins or pin.startswith('Q'):
                readers = self.wire_readers.get(wire, [])
                result.append((wire, readers))
        return result

    def fanin(self, cell_instance):
        """Return list of (wire, driver_cells) that drive this cell."""
        result = []
        conns = self.cell_connections.get(cell_instance, {})
        for pin, wire in conns.items():
            if pin not in {'Q', 'Y', 'X', 'CO', 'S', 'Z'} and not pin.startswith('Q'):
                drivers = self.wire_drivers.get(wire, [])
                result.append((wire, drivers))
        return result

    def get_registers(self):
        """Return all sequential cells (DFFs)."""
        dff_types = {'dfrtp', 'dfstp', 'dfxtp'}
        regs = []
        for cell in self.data['cells']:
            for dt in dff_types:
                if dt in cell['cell_type']:
                    regs.append(cell)
                    break
        return regs

    def get_register_info(self):
        """Detailed register information."""
        regs = self.get_registers()
        result = []
        for r in regs:
            inst = r['instance']
            ctype = r['cell_type']
            conns = r['connections']
            d_wire = conns.get('D', '')
            q_wire = conns.get('Q', '')
            clk_wire = conns.get('CLK', '')
            rst_wire = conns.get('RESET_B', '')

            fanout_targets = self.wire_readers.get(q_wire, [])

            result.append({
                'instance': inst,
                'cell_type': ctype,
                'D': d_wire,
                'Q': q_wire,
                'CLK': clk_wire,
                'RESET_B': rst_wire,
                'fanout_count': len(fanout_targets),
                'fanout_cells': fanout_targets[:10],  # first 10
            })
        return result

    def get_clock_stats(self):
        """Analyze clock connections of all registers."""
        reg_info = self.get_register_info()
        clk_sources = defaultdict(list)
        for r in reg_info:
            clk_sources[r['CLK']].append(r['instance'])
        return dict(clk_sources)

    def get_reset_stats(self):
        """Analyze reset connections of all registers."""
        reg_info = self.get_register_info()
        has_reset = [r for r in reg_info if r['RESET_B']]
        no_reset = [r for r in reg_info if not r['RESET_B']]
        return {
            'with_reset': len(has_reset),
            'without_reset': len(no_reset),
            'reset_sources': list(set(r['RESET_B'] for r in has_reset))
        }

    def stats(self):
        """Overall graph statistics."""
        stats = {
            'total_cells': len(self.data['cells']),
            'total_drivers': len(self.wire_drivers),
            'total_readers': len(self.wire_readers),
            'registers': len(self.get_registers()),
        }
        # Identify unconnected wires
        driven_only = set(self.wire_drivers.keys()) - set(self.wire_readers.keys())
        read_only = set(self.wire_readers.keys()) - set(self.wire_drivers.keys())
        stats['driven_only_wires'] = len(driven_only)
        stats['read_only_wires'] = len(read_only)
        stats['bidirectional_wires'] = len(set(self.wire_drivers.keys()) & set(self.wire_readers.keys()))
        return stats


if __name__ == '__main__':
    infile = sys.argv[1] if len(sys.argv) > 1 else '../data/netlist_parsed.json'
    outfile = sys.argv[2] if len(sys.argv) > 2 else '../data/cell_graph_stats.json'
    regfile = sys.argv[3] if len(sys.argv) > 3 else '../data/register_map.json'

    with open(infile) as f:
        data = json.load(f)

    g = CellGraph(data)

    # Print stats
    s = g.stats()
    print("=== Cell Graph Statistics ===")
    for k, v in s.items():
        print(f"  {k}: {v}")

    # Clock analysis
    clk_stats = g.get_clock_stats()
    print(f"\n=== Clock Domains ===")
    for clk, regs in sorted(clk_stats.items(), key=lambda x: -len(x[1])):
        print(f"  {clk}: {len(regs)} registers")

    # Reset analysis
    rst = g.get_reset_stats()
    print(f"\n=== Reset Analysis ===")
    print(f"  Registers with reset: {rst['with_reset']}")
    print(f"  Registers without reset: {rst['without_reset']}")
    print(f"  Reset signals: {rst['reset_sources']}")

    # Top fanout registers
    reg_info = sorted(g.get_register_info(), key=lambda x: -x['fanout_count'])
    print(f"\n=== Top 10 Highest Fanout Registers ===")
    for r in reg_info[:10]:
        print(f"  {r['instance']} ({r['cell_type']}): D={r['D']}, Q={r['Q']}, fanout={r['fanout_count']}")

    # Save register info
    os.makedirs(os.path.dirname(regfile), exist_ok=True)
    with open(regfile, 'w') as f:
        json.dump(reg_info, f, indent=2)
    print(f"\nRegister info saved to {regfile}")

    # Save stats
    with open(outfile, 'w') as f:
        json.dump(s, f, indent=2)
    print(f"Graph stats saved to {outfile}")
