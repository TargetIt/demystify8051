#!/usr/bin/env python3
"""
Phase 1 — Module Structure Analysis

P1.1: I/O port reverse tracing
P1.2: Register functional clustering
P1.3: Module boundary proposals
P1.4: Bus and datapath identification
"""

import json, sys, os
from collections import defaultdict, Counter

class ModuleAnalyzer:
    def __init__(self, netlist_json, reg_map_json):
        with open(netlist_json) as f:
            self.data = json.load(f)
        with open(reg_map_json) as f:
            self.reg_info = json.load(f)

        self.cells = self.data['cells']
        self.ports = self.data['ports']
        self.wires = self.data['wires']

        # Build indices
        self._build_wire_index()
        self._build_cell_index()

    def _build_wire_index(self):
        self.wire_drivers = defaultdict(list)
        self.wire_readers = defaultdict(list)
        for cell in self.cells:
            inst = cell['instance']
            for pin, wire in cell['connections'].items():
                if pin in ('Q','Y','X','CO','S','Z') or pin.startswith('Q'):
                    self.wire_drivers[wire].append((inst, pin))
                else:
                    self.wire_readers[wire].append((inst, pin))

    def _build_cell_index(self):
        self.cell_by_inst = {c['instance']: c for c in self.cells}

    def _is_driver_pin(self, pin):
        return pin in ('Q','Y','X','CO','S','Z') or pin.startswith('Q')

    def trace_cone_back(self, start_wire, max_depth=3):
        """Trace fan-in cone from a wire backward through combinational logic."""
        visited = set()
        frontier = [start_wire]
        for _ in range(max_depth):
            new_frontier = []
            for w in frontier:
                if w in visited: continue
                visited.add(w)
                for inst, dpin in self.wire_drivers.get(w, []):
                    cell = self.cell_by_inst.get(inst, {})
                    if not cell: continue
                    for pin, pw in cell['connections'].items():
                        if not self._is_driver_pin(pin):
                            if pw not in visited:
                                new_frontier.append(pw)
            frontier = new_frontier
        return visited

    def p1_1_io_analysis(self):
        """P1.1: Trace I/O ports to identify boundary cells."""
        io_map = {}
        for port in self.ports:
            pname = port['name']
            pdirection = port['direction']
            cells_found = set()

            if pdirection == 'input':
                readers = self.wire_readers.get(pname, [])
                cells_found.update(inst for inst, _ in readers)
            elif pdirection == 'output':
                drivers = self.wire_drivers.get(pname, [])
                cells_found.update(inst for inst, _ in drivers)
                # Also trace one more level back
                for inst, _ in drivers:
                    cell = self.cell_by_inst.get(inst, {})
                    for pin, pw in cell.get('connections', {}).items():
                        if not self._is_driver_pin(pin):
                            for di, _ in self.wire_drivers.get(pw, []):
                                cells_found.add(di)
            elif pdirection == 'inout':
                readers = self.wire_readers.get(pname, [])
                drivers = self.wire_drivers.get(pname, [])
                cells_found.update(inst for inst, _ in readers)
                cells_found.update(inst for inst, _ in drivers)

            io_map[pname] = {
                'direction': pdirection,
                'direct_connected_cells': len(cells_found),
                'cells': sorted(cells_found)
            }
        return io_map

    def p1_2_register_clustering(self):
        """P1.2: Cluster registers by shared connectivity patterns.

        Strategy: FF-to-FF connectivity via shared intermediate wires.
        Two registers that share many intermediate wires are likely in the same module.
        """
        reg_cells = {r['instance'] for r in self.reg_info}
        reg_q_wires = {r['instance']: r['Q'] for r in self.reg_info if r['Q']}
        reg_d_wires = {r['instance']: r['D'] for r in self.reg_info if r['D']}

        # Build FF→FF connectivity: for each FF, find which other FFs
        # share wires in their fanin/fanout cones
        ff_connections = defaultdict(Counter)

        for reg_inst in reg_cells:
            q_wire = reg_q_wires.get(reg_inst, '')
            d_wire = reg_d_wires.get(reg_inst, '')

            # Fanout: what other FFs does this FF's Q wire reach?
            if q_wire:
                for target_inst, _ in self.wire_readers.get(q_wire, []):
                    if target_inst in reg_cells and target_inst != reg_inst:
                        ff_connections[reg_inst][target_inst] += 5

            # Fanin: what FFs drive into this FF's D cone?
            if d_wire:
                for driver_inst, _ in self.wire_drivers.get(d_wire, []):
                    if driver_inst in reg_cells and driver_inst != reg_inst:
                        ff_connections[reg_inst][driver_inst] += 3

            # Shared fanout: FFs that share the same target readers
            if q_wire:
                my_readers = set(inst for inst, _ in self.wire_readers.get(q_wire, []))
                for other_reg in reg_cells:
                    if other_reg == reg_inst: continue
                    oq = reg_q_wires.get(other_reg, '')
                    if oq:
                        other_readers = set(inst for inst, _ in self.wire_readers.get(oq, []))
                        shared = my_readers & other_readers
                        if shared:
                            ff_connections[reg_inst][other_reg] += len(shared)

        # Simple clustering: group FFs that have strong mutual connections
        # Use a greedy approach
        clusters = defaultdict(list)
        visited = set()
        threshold = 3  # minimum connection weight to cluster

        # Sort FFs by their total connection weight
        ff_weights = {ff: sum(c.values()) for ff, c in ff_connections.items()}
        sorted_ffs = sorted(ff_weights, key=ff_weights.get, reverse=True)

        cluster_id = 0
        for ff in sorted_ffs:
            if ff in visited:
                continue
            stack = [ff]
            cluster = []
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                cluster.append(current)
                for neighbor, weight in ff_connections.get(current, {}).items():
                    if neighbor not in visited and weight >= threshold:
                        stack.append(neighbor)
            if cluster:
                clusters[f'cluster_{cluster_id}'] = cluster
                cluster_id += 1

        # Map each FF to its cluster
        ff_to_cluster = {}
        for cid, ffs in clusters.items():
            for f in ffs:
                ff_to_cluster[f] = cid

        # Expand clusters to include non-FF cells by proximity
        cluster_cells = defaultdict(set)
        for cid, ffs in clusters.items():
            cluster_cells[cid].update(ffs)
            for ff in ffs:
                cell = self.cell_by_inst.get(ff, {})
                for pin, wire in cell.get('connections', {}).items():
                    for inst, _ in self.wire_drivers.get(wire, []):
                        cluster_cells[cid].add(inst)
                    for inst, _ in self.wire_readers.get(wire, []):
                        cluster_cells[cid].add(inst)

        return {
            'num_clusters': len(clusters),
            'cluster_sizes': {c: len(ffs) for c, ffs in sorted(clusters.items(), key=lambda x: -len(x[1]))},
            'ff_to_cluster': ff_to_cluster,
            'total_clustered': len(visited),
            'unclustered': len(reg_cells) - len(visited),
            'cluster_cell_count': {c: len(cells) for c, cells in sorted(cluster_cells.items(), key=lambda x: -len(x[1]))},
            'clusters': {c: ffs for c, ffs in sorted(clusters.items(), key=lambda x: -len(x[1]))[:20]},
        }

    def p1_3_bus_analysis(self):
        """P1.3: Identify key buses by width, fanout, and connectivity patterns."""
        buses = self.wires['bus']
        bus_info = []
        for bname, binfo in buses.items():
            width = binfo['width']
            # Count total fanout of all bits
            total_fanout = 0
            driver_insts = set()
            reader_insts = set()
            for i in range(binfo['lo'], binfo['hi'] + 1):
                bit_name = f"{bname}[{i}]"
                for inst, _ in self.wire_drivers.get(bit_name, []):
                    driver_insts.add(inst)
                for inst, _ in self.wire_readers.get(bit_name, []):
                    reader_insts.add(inst)
                total_fanout += len(self.wire_readers.get(bit_name, []))

            bus_info.append({
                'name': bname,
                'width': width,
                'drivers': len(driver_insts),
                'readers': len(reader_insts),
                'total_fanout': total_fanout,
                'avg_fanout_per_bit': total_fanout / width if width > 0 else 0,
            })

        bus_info.sort(key=lambda x: -x['total_fanout'])
        return bus_info[:30]

    def p1_4_module_proposal(self, io_data, cluster_data, bus_data):
        """P1.4: Propose module boundaries based on analysis."""
        # Match top clusters to known 8051 modules
        spec_modules = [
            ('cpu_core', ['ALU', 'Decoder', 'Control', 'Register File', 'PSW']),
            ('alu', ['8-bit ALU', 'arithmetic', 'logic']),
            ('decoder', ['instruction decoder', 'opcode', 'microcode']),
            ('control_fsm', ['state machine', 'control', 'sequence']),
            ('reg_file', ['register file', 'register bank', 'R0-R7']),
            ('iram', ['internal RAM', '128B', 'data memory']),
            ('sfr_block', ['SFR', 'special function register']),
            ('timer', ['timer', 'counter', 'T0', 'T1']),
            ('uart', ['UART', 'serial', 'baud']),
            ('intc', ['interrupt', 'priority', 'vector']),
            ('io_ports', ['I/O port', 'P0', 'P1', 'P2', 'P3']),
            ('prom', ['program ROM', 'instruction memory']),
        ]

        return {
            'num_clusters_found': cluster_data['num_clusters'],
            'total_ffs_clustered': cluster_data['total_clustered'],
            'unclustered_ffs': cluster_data['unclustered'],
            'top_cluster_sizes': dict(list(cluster_data['cluster_sizes'].items())[:12]),
            'high_fanout_buses': [(b['name'], b['width'], b['total_fanout']) for b in bus_data[:10]],
            'io_connections': {k: v['direct_connected_cells'] for k, v in sorted(io_data.items())},
        }


if __name__ == '__main__':
    infile = sys.argv[1] if len(sys.argv) > 1 else '../data/netlist_parsed.json'
    regfile = sys.argv[2] if len(sys.argv) > 2 else '../data/register_map.json'
    outdir = sys.argv[3] if len(sys.argv) > 3 else '../data'

    a = ModuleAnalyzer(infile, regfile)

    # P1.1
    print("=== P1.1 I/O Port Analysis ===")
    io = a.p1_1_io_analysis()
    for pname, info in io.items():
        print(f"  {pname} ({info['direction']}): {info['direct_connected_cells']} cells connected")

    # P1.2
    print("\n=== P1.2 Register Clustering ===")
    clusters = a.p1_2_register_clustering()
    print(f"  Found {clusters['num_clusters']} clusters")
    print(f"  Clustered: {clusters['total_clustered']}/{1626} FFs")
    print(f"  Unclustered: {clusters['unclustered']}")
    print(f"  Top clusters (by FF count):")
    for cid, count in list(clusters['cluster_sizes'].items())[:12]:
        print(f"    {cid}: {count} FFs, {clusters['cluster_cell_count'].get(cid, '?')} total cells")

    # P1.3
    print("\n=== P1.3 Bus Analysis ===")
    buses = a.p1_3_bus_analysis()
    print("  Top 15 buses by fanout:")
    for b in buses[:15]:
        print(f"    {b['name']}: {b['width']}b, {b['drivers']} drivers, {b['readers']} readers, avg fanout={b['avg_fanout_per_bit']:.1f}")

    # P1.4
    print("\n=== P1.4 Module Boundary Proposal ===")
    proposal = a.p1_4_module_proposal(io, clusters, buses)
    for k, v in proposal.items():
        print(f"  {k}: {v}")

    # Save outputs
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, 'io_boundary.json'), 'w') as f:
        json.dump(io, f, indent=2)
    with open(os.path.join(outdir, 'register_clusters.json'), 'w') as f:
        json.dump(clusters, f, indent=2)
    with open(os.path.join(outdir, 'bus_info.json'), 'w') as f:
        json.dump(buses, f, indent=2)
    with open(os.path.join(outdir, 'module_proposal.json'), 'w') as f:
        json.dump(proposal, f, indent=2)
    print(f"\nSaved analysis data to {outdir}/")
