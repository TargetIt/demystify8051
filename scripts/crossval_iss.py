#!/usr/bin/env python3
"""Run the Python ISS and dump per-instruction state for cross-validation."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'model'))

from python.echo_8051 import Echo8051

# Test program — same as RTL PROM test
# Each instruction is hand-assembled
PROGRAM = bytes([
    0x74, 0x42,       # MOV A,#0x42          → A=0x42
    0x78, 0x55,       # MOV R0,#0x55         → R0=0x55
    0x79, 0x33,       # MOV R1,#0x33         → R1=0x33
    0xE8,             # MOV A,R0             → A=0x55
    0x24, 0x20,       # ADD A,#0x20          → A=0x75
    0xC3,             # CLR C
    0x94, 0x25,       # SUBB A,#0x25         → A=0x50
    0x54, 0x0F,       # ANL A,#0x0F          → A=0x00
    0x44, 0xAA,       # ORL A,#0xAA          → A=0xAA
    0x64, 0x55,       # XRL A,#0x55          → A=0xFF
    0x04,             # INC A                → A=0x00
    0x14,             # DEC A                → A=0xFF
    0x04,             # INC A                → A=0x00
    0x04,             # INC A                → A=0x01
    0x04,             # INC A                → A=0x02
    0xC4,             # SWAP A               → A=0x20
    0xF4,             # CPL A                → A=0xDF
    0xE4,             # CLR A                → A=0x00
    0x74, 0x0A,       # MOV A,#10
    0x75, 0xF0, 0x06, # MOV B,#6
    0xA4,             # MUL AB               → A=60=0x3C
    0xF5, 0x90,       # MOV P1,A
    0x74, 0x0F,       # MOV A,#15
    0x75, 0xF0, 0x04, # MOV B,#4
    0x84,             # DIV AB               → A=3
    0xF5, 0xA0,       # MOV P2,A
    0x78, 0x03,       # MOV R0,#3
    0xE4,             # CLR A                → A=0
    0x04,             # INC A    (loop: addr 34)
    0xD8, 0xFD,       # DJNZ R0,-3           → A=3 after loop
    0xF5, 0xB0,       # MOV P3,A
    # Push/Pop
    0xC0, 0xE0,       # PUSH ACC (A=3)
    0xE4,             # CLR A
    0xD0, 0xE0,       # POP ACC              → A=3
    0xF5, 0x80,       # MOV P0,A
    # Bit ops
    0xD3,             # SETB C
    0xC3,             # CLR C
    0xB3,             # CPL C
    # SJMP loop
    0x80, 0xFE,       # SJMP $ (infinite loop)
])

def run_trace():
    cpu = Echo8051(rom_size=4096)
    cpu.load_bytes(PROGRAM)

    out = sys.stdout
    out.write("# ISS instruction trace\n")
    out.write("# format: INSTR_NUM|PC|ACC|PSW|SP\n")

    instr_num = 0
    seen_pcs = set()
    max_instr = 200

    while instr_num < max_instr:
        pc_before = cpu.get_pc()
        cycles = cpu.step()
        instr_num += 1

        state = cpu.get_state()
        acc = state['acc']
        psw = state['psw']
        sp  = state['sp']
        pc  = state['pc']

        out.write(f"{instr_num}|{pc:04X}|{acc:02X}|{psw:02X}|{sp:02X}|\n")

        # Detect infinite loop (SJMP $)
        if pc_before == cpu.get_pc() and cycles > 1:
            # Same PC means we're stuck in SJMP loop
            break

    out.write(f"# Total: {instr_num} instructions\n")

if __name__ == '__main__':
    run_trace()
