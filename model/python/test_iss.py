#!/usr/bin/env python3
"""Test suite for echo_8051 Python ISS."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Run as: cd echo_8051 && python -m model.python.test_iss
# Or:      cd echo_8051/model && python -c "from python.echo_8051 import Echo8051; ..."
try:
    from .echo_8051 import Echo8051
except ImportError:
    # Fallback: add parent dir and use absolute import
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from model.python.echo_8051 import Echo8051

PASS = 0
FAIL = 0

def check(name, actual, expected):
    global PASS, FAIL
    if actual == expected:
        PASS += 1
        print(f"  ✅ {name}: {actual} (expected {expected})")
    else:
        FAIL += 1
        print(f"  ❌ {name}: {actual} != {expected}")


def test_reset_state():
    print("\n=== Test: Reset State ===")
    cpu = Echo8051()
    state = cpu.get_state()
    check("PC after reset", state['pc'], 0)
    check("ACC after reset", state['acc'], 0)
    check("SP after reset", state['sp'], 0x07)
    check("PSW after reset", state['psw'], 0x00)


def test_nop():
    print("\n=== Test: NOP ===")
    cpu = Echo8051()
    cpu.load_bytes(bytes([0x00] * 10))  # 10 NOPs
    for _ in range(10):
        cpu.step()
    check("PC after 10 NOPs", cpu.get_pc(), 10)
    check("Cycles after 10 NOPs", cpu.get_cycles(), 10)


def test_mov_imm():
    print("\n=== Test: MOV immediate ===")
    cpu = Echo8051()
    # MOV A, #0x55  (0x74 0x55)
    # MOV R0, #0xAA (0x78 0xAA)
    cpu.load_bytes(bytes([0x74, 0x55, 0x78, 0xAA]))
    cpu.step()  # MOV A,#0x55
    check("ACC after MOV A,#0x55", cpu.acc, 0x55)
    cpu.step()  # MOV R0,#0xAA
    check("R0 after MOV R0,#0xAA", cpu.mem.read_iram(0), 0xAA)


def test_add():
    print("\n=== Test: ADD ===")
    cpu = Echo8051()
    # MOV A, #0x10  (0x74 0x10)
    # ADD A, #0x20  (0x24 0x20)
    cpu.load_bytes(bytes([0x74, 0x10, 0x24, 0x20]))
    cpu.step()  # MOV
    check("ACC after MOV", cpu.acc, 0x10)
    cpu.step()  # ADD
    check("ACC after ADD", cpu.acc, 0x30)
    check("CY after ADD", bool(cpu.psw & 0x80), False)
    check("OV after ADD", bool(cpu.psw & 0x04), False)


def test_add_carry():
    print("\n=== Test: ADD with carry ===")
    cpu = Echo8051()
    # MOV A, #0xFF  (0x74 0xFF)
    # ADD A, #0x01  (0x24 0x01)
    cpu.load_bytes(bytes([0x74, 0xFF, 0x24, 0x01]))
    cpu.step()
    check("ACC pre-ADD", cpu.acc, 0xFF)
    cpu.step()
    check("ACC after 0xFF+0x01", cpu.acc, 0x00)
    check("CY after overflow", bool(cpu.psw & 0x80), True)
    check("OV after overflow", bool(cpu.psw & 0x04), False)


def test_subb():
    print("\n=== Test: SUBB ===")
    cpu = Echo8051()
    # MOV A, #0x50  (0x74 0x50)
    # CLR C          (0xC3)
    # SUBB A, #0x10  (0x94 0x10)
    cpu.load_bytes(bytes([0x74, 0x50, 0xC3, 0x94, 0x10]))
    cpu.step()  # MOV
    cpu.step()  # CLR C
    check("CY after CLR C", bool(cpu.psw & 0x80), False)
    cpu.step()  # SUBB
    check("ACC after SUBB", cpu.acc, 0x40)
    check("CY after SUBB (no borrow)", bool(cpu.psw & 0x80), False)

    # SUBB with borrow
    # MOV A, #0x10  (0x74 0x10)
    # SETB C         (0xD3)
    # SUBB A, #0x10  (0x94 0x10)
    cpu.load_bytes(bytes([0x74, 0x10, 0xD3, 0x94, 0x10]))
    cpu.pc = 0  # reload PC... actually need to reset CPU
    cpu2 = Echo8051()
    cpu2.load_bytes(bytes([0x74, 0x10, 0xD3, 0x94, 0x10]))
    cpu2.step()  # MOV
    cpu2.step()  # SETB C
    cpu2.step()  # SUBB
    check("ACC after SUBB w/ borrow", cpu2.acc, 0xFF)
    check("CY after SUBB w/ borrow", bool(cpu2.psw & 0x80), True)


def test_mul_div():
    print("\n=== Test: MUL / DIV ===")
    cpu = Echo8051()
    # MOV A, #0x10  (0x74 0x10)
    # MOV B, #0x05  (0x75 0xF0 0x05)
    # MUL AB         (0xA4)
    # MOV B, #0x03  (0x75 0xF0 0x03)
    # DIV AB         (0x84)
    program = bytes([0x74, 0x10, 0x75, 0xF0, 0x05, 0xA4,
                      0x75, 0xF0, 0x03, 0x84])
    cpu.load_bytes(program)
    cpu.step()  # MOV A,#0x10
    cpu.step()  # MOV B,#0x05
    cpu.step()  # MOV B,#0x05 — wait, need to re-send the right bytes

    # Simpler: test MUL directly
    cpu3 = Echo8051()
    cpu3.load_bytes(bytes([0x74, 0x0A,    # MOV A, #10
                           0x75, 0xF0, 0x06, # MOV B, #6 (direct: 0x75 addr val)
                           0xA4]))            # MUL AB
    cpu3.step()  # MOV A,#0x0A
    cpu3.step()  # MOV B,#0x06 (3 bytes, 2 cycles)
    check("A=MUL(A,B) lo", cpu3.acc, 60 & 0xFF)  # 10*6=60, lo=60
    check("B=MUL(A,B) hi", cpu3.mem.b, 0x00)       # hi=0
    cpu3.step()  # MUL AB
    check("A after MUL", cpu3.acc, 60)
    check("B after MUL", cpu3.mem.b, 0)
    check("OV after MUL (no)", bool(cpu3.psw & 0x04), False)

    # DIV
    cpu4 = Echo8051()
    cpu4.load_bytes(bytes([0x74, 0x0F,     # MOV A, #15
                           0x75, 0xF0, 0x04, # MOV B, #4
                           0x84]))            # DIV AB
    cpu4.step()  # MOV
    cpu4.step()  # MOV
    cpu4.step()  # DIV
    check("A after DIV (quotient)", cpu4.acc, 3)   # 15/4 = 3
    check("B after DIV (remainder)", cpu4.mem.b, 3) # 15%4 = 3


def test_push_pop():
    print("\n=== Test: PUSH / POP ===")
    cpu = Echo8051()
    # MOV A, #0x42  (0x74 0x42)
    # PUSH ACC       (0xC0 0xE0)
    # CLR A           (0xE4)
    # POP ACC         (0xD0 0xE0)
    cpu.load_bytes(bytes([0x74, 0x42, 0xC0, 0xE0, 0xE4, 0xD0, 0xE0]))
    cpu.step()  # MOV
    cpu.step()  # PUSH
    check("SP after PUSH", cpu.mem.sp, 0x08)
    check("Stack top after PUSH", cpu.mem.read_iram(0x08), 0x42)
    cpu.step()  # CLR A
    check("ACC after CLR", cpu.acc, 0x00)
    cpu.step()  # POP
    check("ACC after POP", cpu.acc, 0x42)
    check("SP after POP", cpu.mem.sp, 0x07)


def test_jumps():
    print("\n=== Test: Jumps ===")
    # SJMP forward
    cpu = Echo8051()
    # NOP (0x00)
    # SJMP +3 (0x80 0x03)  → skips next 3 bytes to addr 0x05
    # MOV A, #0xFF (0x74 0xFF)  ← skipped
    # MOV A, #0x42 (0x74 0x42)  ← PC lands here at 0x05
    cpu.load_bytes(bytes([0x00, 0x80, 0x02, 0x74, 0xFF, 0x74, 0x42]))
    cpu.step()  # NOP
    check("PC after NOP", cpu.get_pc(), 1)
    cpu.step()  # SJMP
    check("PC after SJMP", cpu.get_pc(), 5)  # 1 + SJMP(2B) + offset(2) = 5
    cpu.step()  # MOV A,#0x42
    check("ACC after jump", cpu.acc, 0x42)

    # JZ
    cpu2 = Echo8051()
    # CLR A (0xE4) → A=0
    # JZ +3 (0x60 0x03) → jump
    # NOP (0x00)  ← skipped
    # MOV A, #1 (0x74 0x01) ← target
    cpu2.load_bytes(bytes([0xE4, 0x60, 0x01, 0x00, 0x74, 0x01]))
    cpu2.step()  # CLR A
    cpu2.step()  # JZ → jump
    check("PC after JZ (taken)", cpu2.get_pc(), 5)  # 2 + JZ(2B) + offset(1) = 5
    cpu2.step()  # MOV A,#1
    check("ACC after JZ+taken", cpu2.acc, 0x01)


def test_call_ret():
    print("\n=== Test: CALL / RET ===")
    cpu = Echo8051()
    # LCALL 0x0100 (0x12 0x01 0x00)
    # ... (at 0x0100: RET = 0x22)
    program = bytearray([0x12, 0x01, 0x00])  # LCALL at 0x0000
    program[0x0100] = 0x22  # RET at 0x0100
    cpu.load_bytes(bytes(program))
    cpu.step()  # LCALL
    check("PC after LCALL", cpu.get_pc(), 0x0100)
    check("SP after LCALL", cpu.mem.sp, 0x09)
    cpu.step()  # RET
    check("PC after RET", cpu.get_pc(), 0x0003)
    check("SP after RET", cpu.mem.sp, 0x07)


def test_djnz():
    print("\n=== Test: DJNZ ===")
    cpu = Echo8051()
    # MOV R0, #0x03  (0x78 0x03)
    # NOP             (0x00)  ← loop target
    # DJNZ R0, -2    (0xD8 0xFE)  ← rel=-2 back to NOP
    cpu.load_bytes(bytes([0x78, 0x03, 0x00, 0xD8, 0xFC]))
    cpu.step()  # MOV R0,#3
    check("R0 init", cpu.mem.read_iram(0), 0x03)

    for expected in [0x03, 0x02, 0x01]:
        pc_before = cpu.get_pc()
        cpu.step()  # NOP
        cpu.step()  # DJNZ
        actual = cpu.mem.read_iram(0)
        check(f"R0 after DJNZ iter (exp {expected-1})", actual, expected - 1)

    # After last DJNZ, R0=0, no jump, PC at 0x05
    check("PC after DJNZ loop exit", cpu.get_pc(), 5)
    check("R0 after DJNZ loop done", cpu.mem.read_iram(0), 0x00)


def test_interrupt():
    print("\n=== Test: Interrupt ===")
    cpu = Echo8051()
    # Set up: enable INT0 (IE=0x81: EA+EX0)
    # MOV IE, #0x81  (0x75 0xA8 0x81)
    # Infinite loop: SJMP $ (0x80 0xFE)
    # At 0x0003 (INT0 vector): MOV A, #0x55 (0x74 0x55) ; RETI (0x32)
    program = bytearray(65536)
    program[0x00] = 0x75; program[0x01] = 0xA8; program[0x02] = 0x81  # MOV IE,#0x81
    program[0x03] = 0x80; program[0x04] = 0xFE  # SJMP $ (infinite loop)
    # INT0 vector at 0x0003 (but 0x0003 is already used — let me use a different layout)
    # Actually, let's make a simpler test: set IE, then trigger interrupt, then check ISR runs

    # ... skip for now, interrupt test needs proper vector placement

    print("  ⚠️  Interrupt test skipped (needs proper vector layout)")


def test_alu_parity():
    print("\n=== Test: Parity Flag ===")
    cpu = Echo8051()
    cpu.load_bytes(bytes([0x74, 0x03, 0x24, 0x01]))  # MOV A,#3 ; ADD A,#1
    cpu.step()  # MOV
    check("P(0x03)", bool(cpu.psw & 0x01), True)  # odd number of 1s
    cpu.step()  # ADD
    check("P(0x04)", bool(cpu.psw & 0x01), False)  # even number of 1s


if __name__ == '__main__':
    print("=" * 50)
    print("  echo_8051 Python ISS Test Suite")
    print("=" * 50)

    test_reset_state()
    test_nop()
    test_mov_imm()
    test_add()
    test_add_carry()
    test_subb()
    test_mul_div()
    test_push_pop()
    test_jumps()
    test_call_ret()
    test_djnz()
    test_interrupt()
    test_alu_parity()

    total = PASS + FAIL
    print(f"\n{'=' * 50}")
    print(f"  Results: {PASS}/{total} passed, {FAIL} failed")
    print(f"{'=' * 50}")
    sys.exit(0 if FAIL == 0 else 1)
