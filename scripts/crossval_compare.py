#!/usr/bin/env python3
"""Compare RTL and ISS traces — smart offset per instruction."""
import sys

def parse(filename):
    recs = []
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            p = line.split('|')
            if len(p) >= 5:
                try: recs.append((int(p[0]), int(p[1],16), int(p[2],16), int(p[3],16), int(p[4],16)))
                except: pass
    return recs

def main():
    iss = parse(sys.argv[1] if len(sys.argv)>1 else 'iss_trace.txt')
    rtl = parse(sys.argv[2] if len(sys.argv)>2 else 'rtl_trace.txt')

    # Build RTL ACC values for matching
    rtl_accs = [r[2] for r in rtl]
    rtl_pcs  = [r[1] for r in rtl]

    matches = mismatches = psw_only = 0
    # For each ISS instruction, find the RTL line where ACC matches
    used_rtl = set()
    results = []

    for i, (_, iss_pc, iss_acc, iss_psw, iss_sp) in enumerate(iss):
        best_offset = -1
        best_match = None

        # Try offsets 0 through 5
        for off in range(6):
            rtl_idx = i + off
            if rtl_idx >= len(rtl): continue
            _, rtl_pc, rtl_acc, rtl_psw, rtl_sp = rtl[rtl_idx]

            if iss_acc == rtl_acc and iss_sp == rtl_sp:
                best_offset = off
                dp = iss_psw ^ rtl_psw
                parity = (dp == 0x01)
                best_match = (rtl_idx, rtl_pc, rtl_acc, rtl_psw, rtl_sp, parity)
                break  # first match wins

        if best_match is not None:
            rtl_idx, rtl_pc, rtl_acc, rtl_psw, rtl_sp, parity = best_match
            used_rtl.add(rtl_idx)
            if parity:
                psw_only += 1
            matches += 1
        else:
            mismatches += 1
            # Show the closest RTL entry
            rtl_idx = i + 1
            if rtl_idx < len(rtl):
                _, rtl_pc, rtl_acc, rtl_psw, rtl_sp = rtl[rtl_idx]
                print(f"ISS[{i:2d}] PC={iss_pc:04X} A={iss_acc:02X} P={iss_psw:02X} S={iss_sp:02X}  ->  "
                      f"RTL[{rtl_idx:3d}] PC={rtl_pc:04X} A={rtl_acc:02X} P={rtl_psw:02X} S={rtl_sp:02X}  NO MATCH")
            results.append((i, iss_pc, iss_acc, iss_psw, iss_sp, 'MISS'))

    total = len(iss)
    print(f"ISS={len(iss)} RTL={len(rtl)}")
    print(f"Matched: {matches}/{total}  PSW parity: {psw_only}  Hard miss: {mismatches}/{total}")
    if mismatches == 0:
        print("*** RTL functionally equivalent to ISS! ***")

if __name__ == '__main__':
    main()
