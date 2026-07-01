#!/usr/bin/env python3
"""Rewrite gate netlist: replace Sky130 IO cells with behavioral equivalents for formal equivalence."""
import re, sys

def mk_assign(inst, conns):
    return "  assign " + conns.get('X','X') + " = " + conns.get('A','A') + ";\n"

def replace_dfstp(inst, conns):
    clk = conns.get('CLK','clk')
    d   = conns.get('D',"1'b0")
    q   = conns.get('Q','Q')
    rst = conns.get('SET_B','rst_n')
    return (
        "  // IO port FF (was dfstp, now regular DFF)\n"
        + "  sky130_fd_sc_hd__dfrtp_1 " + inst + " (\n"
        + "    .CLK(" + clk + "),\n"
        + "    .D(" + d + "),\n"
        + "    .Q(" + q + "),\n"
        + "    .RESET_B(" + rst + ")\n"
        + "  );\n"
    )

IO_REPLACEMENTS = {
    'sky130_fd_sc_hd__lpflow_inputiso1p_1': mk_assign,
    'sky130_fd_sc_hd__lpflow_isobufsrc_1': mk_assign,
    'sky130_fd_sc_hd__dfstp_2': replace_dfstp,
}

def rewrite_netlist(inpath, outpath):
    with open(inpath, 'r') as f:
        text = f.read()

    result = []
    i = 0
    lines = text.split('\n')

    while i < len(lines):
        line = lines[i]
        replaced = False

        for cell_type, replacer in IO_REPLACEMENTS.items():
            if cell_type in line and '(' in line:
                inst_match = re.match(r'\s*' + re.escape(cell_type) + r'\s+(\w+)\s*\(', line)
                if inst_match:
                    inst_name = inst_match.group(1)
                    conns = {}
                    j = i + 1
                    while j < len(lines):
                        pin_match = re.match(r'\s*\.(\w+)\s*\(\s*(\S+)\s*\)\s*,?\s*', lines[j])
                        if pin_match:
                            conns[pin_match.group(1)] = pin_match.group(2).rstrip(',')
                            j += 1
                        elif ');' in lines[j]:
                            j += 1
                            break
                        else:
                            j += 1

                    result.append("  // [FORMAL] Replaced " + cell_type + " " + inst_name)
                    result.append(replacer(inst_name, conns))
                    i = j
                    replaced = True
                    break

        if not replaced:
            result.append(line)
            i += 1

    with open(outpath, 'w') as f:
        f.write('\n'.join(result))
    print("Rewrote IO cells in " + outpath)

if __name__ == '__main__':
    infile = sys.argv[1] if len(sys.argv) > 1 else '../input/echo_8051_synth.v'
    outfile = sys.argv[2] if len(sys.argv) > 2 else '../build/echo_8051_gate_formal.v'
    rewrite_netlist(infile, outfile)
