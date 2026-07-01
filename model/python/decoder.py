"""8051 Instruction Decoder: opcode table + decoding logic."""

from dataclasses import dataclass
from typing import Callable, Optional, Any

@dataclass
class InstrInfo:
    mnemonic: str
    bytes: int          # 1, 2, or 3
    cycles: int         # machine cycles (12 oscillator clocks each)
    handler: Callable   # (cpu, opcode) -> None

    @staticmethod
    def invalid(opcode: int) -> 'InstrInfo':
        return InstrInfo(f"???_{opcode:02X}", 1, 1, _nop_handler)


# ===== Instruction handlers (imported by CPU core) =====

def _nop_handler(cpu, opcode: int) -> None:
    pass

def _invalid_handler(cpu, opcode: int) -> None:
    # Treat undefined opcodes as NOP
    pass

# Handlers are methods on the CPU class, registered via opcode table.
# We define them as standalone functions that take (cpu, opcode).


# ===== OPCODE TABLE =====
# Maps opcode -> InstrInfo. Populated below.

OPCODES: dict[int, InstrInfo] = {}


def _reg(opcode: int, mnemonic: str, cycles: int, handler: Callable,
         nbytes: int = 1):
    OPCODES[opcode] = InstrInfo(mnemonic, nbytes, cycles, handler)


def build_opcode_table():
    """Build the complete 255-entry opcode table."""
    # Import here to avoid circular imports
    from . import instructions as ins

    # ==== NOP (0x00) ====
    _reg(0x00, "NOP", 1, ins.nop)

    # ==== AJMP page0 (0x01-0x1F, odd) ====
    for i in range(8):
        _reg(0x01 + i*2, "AJMP", 2, ins.ajmp, 2)
    # ==== LJMP (0x02) ====
    _reg(0x02, "LJMP", 2, ins.ljmp, 3)

    # ==== RR A (0x03) ====
    _reg(0x03, "RR A", 1, ins.rr_a)

    # ==== INC A (0x04) ====
    _reg(0x04, "INC A", 1, ins.inc_a)

    # ==== INC direct (0x05) ====
    _reg(0x05, "INC direct", 1, ins.inc_direct, 2)

    # ==== INC @R0 (0x06), INC @R1 (0x07) ====
    _reg(0x06, "INC @R0", 1, ins.inc_iR0)
    _reg(0x07, "INC @R1", 1, ins.inc_iR1)

    # ==== INC R0-R7 (0x08-0x0F) ====
    for r in range(8):
        _reg(0x08 + r, f"INC R{r}", 1, ins.inc_rn(r))

    # ==== JBC bit,rel (0x10) ====
    _reg(0x10, "JBC bit,rel", 2, ins.jbc, 3)

    # ==== ACALL page0 (0x11-0x1F, odd) ====
    for i in range(8):
        _reg(0x11 + i*2, "ACALL", 2, ins.acall, 2)

    # ==== LCALL (0x12) ====
    _reg(0x12, "LCALL", 2, ins.lcall, 3)

    # ==== RRC A (0x13) ====
    _reg(0x13, "RRC A", 1, ins.rrc_a)

    # ==== DEC A (0x14) ====
    _reg(0x14, "DEC A", 1, ins.dec_a)

    # ==== DEC direct (0x15) ====
    _reg(0x15, "DEC direct", 1, ins.dec_direct, 2)

    # ==== DEC @R0/@R1 (0x16-0x17) ====
    _reg(0x16, "DEC @R0", 1, ins.dec_iR0)
    _reg(0x17, "DEC @R1", 1, ins.dec_iR1)

    # ==== DEC R0-R7 (0x18-0x1F) ====
    for r in range(8):
        _reg(0x18 + r, f"DEC R{r}", 1, ins.dec_rn(r))

    # ==== JB bit,rel (0x20) ====
    _reg(0x20, "JB bit,rel", 2, ins.jb, 3)

    # ==== AJMP page1 (0x21-0x3F, odd) ====
    for i in range(16):
        _reg(0x21 + i*2, "AJMP", 2, ins.ajmp, 2)

    # ==== RET (0x22) ====
    _reg(0x22, "RET", 2, ins.ret)

    # ==== RL A (0x23) ====
    _reg(0x23, "RL A", 1, ins.rl_a)

    # ==== ADD A,#imm (0x24) ====
    _reg(0x24, "ADD A,#data", 1, ins.add_a_imm, 2)

    # ==== ADD A,direct (0x25) ====
    _reg(0x25, "ADD A,direct", 1, ins.add_a_direct, 2)

    # ==== ADD A,@R0/@R1 (0x26-0x27) ====
    _reg(0x26, "ADD A,@R0", 1, ins.add_a_iR0)
    _reg(0x27, "ADD A,@R1", 1, ins.add_a_iR1)

    # ==== ADD A,R0-R7 (0x28-0x2F) ====
    for r in range(8):
        _reg(0x28 + r, f"ADD A,R{r}", 1, ins.add_a_rn(r))

    # ==== JNB bit,rel (0x30) ====
    _reg(0x30, "JNB bit,rel", 2, ins.jnb, 3)

    # ==== ACALL page1 (0x31-0x3F, odd) ====
    for i in range(8):
        _reg(0x31 + i*2, "ACALL", 2, ins.acall, 2)

    # ==== RETI (0x32) ====
    _reg(0x32, "RETI", 2, ins.reti)

    # ==== RLC A (0x33) ====
    _reg(0x33, "RLC A", 1, ins.rlc_a)

    # ==== ADDC A,#imm (0x34) ====
    _reg(0x34, "ADDC A,#data", 1, ins.addc_a_imm, 2)

    # ==== ADDC A,direct (0x35) ====
    _reg(0x35, "ADDC A,direct", 1, ins.addc_a_direct, 2)

    # ==== ADDC A,@R0/@R1 (0x36-0x37) ====
    _reg(0x36, "ADDC A,@R0", 1, ins.addc_a_iR0)
    _reg(0x37, "ADDC A,@R1", 1, ins.addc_a_iR1)

    # ==== ADDC A,R0-R7 (0x38-0x3F) ====
    for r in range(8):
        _reg(0x38 + r, f"ADDC A,R{r}", 1, ins.addc_a_rn(r))

    # ==== JC rel (0x40) ====
    _reg(0x40, "JC rel", 2, ins.jc, 2)

    # ==== AJMP page2 (0x41-0x5F, odd) ====
    for i in range(16):
        _reg(0x41 + i*2, "AJMP", 2, ins.ajmp, 2)

    # ==== ORL direct,A (0x42) ====
    _reg(0x42, "ORL direct,A", 1, ins.orl_direct_a, 2)

    # ==== ORL direct,#imm (0x43) ====
    _reg(0x43, "ORL direct,#data", 2, ins.orl_direct_imm, 3)

    # ==== ORL A,#imm (0x44) ====
    _reg(0x44, "ORL A,#data", 1, ins.orl_a_imm, 2)

    # ==== ORL A,direct (0x45) ====
    _reg(0x45, "ORL A,direct", 1, ins.orl_a_direct, 2)

    # ==== ORL A,@R0/@R1 (0x46-0x47) ====
    _reg(0x46, "ORL A,@R0", 1, ins.orl_a_iR0)
    _reg(0x47, "ORL A,@R1", 1, ins.orl_a_iR1)

    # ==== ORL A,R0-R7 (0x48-0x4F) ====
    for r in range(8):
        _reg(0x48 + r, f"ORL A,R{r}", 1, ins.orl_a_rn(r))

    # ==== JNC rel (0x50) ====
    _reg(0x50, "JNC rel", 2, ins.jnc, 2)

    # ==== ACALL page2 (0x51-0x5F, odd) ====
    for i in range(8):
        _reg(0x51 + i*2, "ACALL", 2, ins.acall, 2)

    # ==== ANL direct,A (0x52) ====
    _reg(0x52, "ANL direct,A", 1, ins.anl_direct_a, 2)

    # ==== ANL direct,#imm (0x53) ====
    _reg(0x53, "ANL direct,#data", 2, ins.anl_direct_imm, 3)

    # ==== ANL A,#imm (0x54) ====
    _reg(0x54, "ANL A,#data", 1, ins.anl_a_imm, 2)

    # ==== ANL A,direct (0x55) ====
    _reg(0x55, "ANL A,direct", 1, ins.anl_a_direct, 2)

    # ==== ANL A,@R0/@R1 (0x56-0x57) ====
    _reg(0x56, "ANL A,@R0", 1, ins.anl_a_iR0)
    _reg(0x57, "ANL A,@R1", 1, ins.anl_a_iR1)

    # ==== ANL A,R0-R7 (0x58-0x5F) ====
    for r in range(8):
        _reg(0x58 + r, f"ANL A,R{r}", 1, ins.anl_a_rn(r))

    # ==== JZ rel (0x60) ====
    _reg(0x60, "JZ rel", 2, ins.jz, 2)

    # ==== AJMP page3 (0x61-0x7F, odd) ====
    for i in range(16):
        _reg(0x61 + i*2, "AJMP", 2, ins.ajmp, 2)

    # ==== XRL direct,A (0x62) ====
    _reg(0x62, "XRL direct,A", 1, ins.xrl_direct_a, 2)

    # ==== XRL direct,#imm (0x63) ====
    _reg(0x63, "XRL direct,#data", 2, ins.xrl_direct_imm, 3)

    # ==== XRL A,#imm (0x64) ====
    _reg(0x64, "XRL A,#data", 1, ins.xrl_a_imm, 2)

    # ==== XRL A,direct (0x65) ====
    _reg(0x65, "XRL A,direct", 1, ins.xrl_a_direct, 2)

    # ==== XRL A,@R0/@R1 (0x66-0x67) ====
    _reg(0x66, "XRL A,@R0", 1, ins.xrl_a_iR0)
    _reg(0x67, "XRL A,@R1", 1, ins.xrl_a_iR1)

    # ==== XRL A,R0-R7 (0x68-0x6F) ====
    for r in range(8):
        _reg(0x68 + r, f"XRL A,R{r}", 1, ins.xrl_a_rn(r))

    # ==== JNZ rel (0x70) ====
    _reg(0x70, "JNZ rel", 2, ins.jnz, 2)

    # ==== ACALL page3 (0x71-0x7F, odd) ====
    for i in range(8):
        _reg(0x71 + i*2, "ACALL", 2, ins.acall, 2)

    # ==== ORL C,bit (0x72) ====
    _reg(0x72, "ORL C,bit", 2, ins.orl_c_bit, 2)

    # ==== JMP @A+DPTR (0x73) ====
    _reg(0x73, "JMP @A+DPTR", 2, ins.jmp_adptr)

    # ==== MOV A,#imm (0x74) ====
    _reg(0x74, "MOV A,#data", 1, ins.mov_a_imm, 2)

    # ==== MOV direct,#imm (0x75) ====
    _reg(0x75, "MOV direct,#data", 2, ins.mov_direct_imm, 3)

    # ==== MOV @R0/#imm, @R1/#imm (0x76-0x77) ====
    _reg(0x76, "MOV @R0,#data", 1, ins.mov_iR0_imm, 2)
    _reg(0x77, "MOV @R1,#data", 1, ins.mov_iR1_imm, 2)

    # ==== MOV R0-R7,#imm (0x78-0x7F) ====
    for r in range(8):
        _reg(0x78 + r, f"MOV R{r},#data", 1, ins.mov_rn_imm(r), 2)

    # ==== SJMP (0x80) ====
    _reg(0x80, "SJMP", 2, ins.sjmp, 2)

    # ==== AJMP page4 (0x81-0x9F, odd) ====
    for i in range(16):
        _reg(0x81 + i*2, "AJMP", 2, ins.ajmp, 2)

    # ==== ANL C,bit (0x82) ====
    _reg(0x82, "ANL C,bit", 2, ins.anl_c_bit, 2)

    # ==== MOVC A,@A+PC (0x83) ====
    _reg(0x83, "MOVC A,@A+PC", 2, ins.movc_a_apc)

    # ==== DIV AB (0x84) ====
    _reg(0x84, "DIV AB", 4, ins.div_ab)

    # ==== MOV direct,direct (0x85) ====
    _reg(0x85, "MOV direct,direct", 2, ins.mov_direct_direct, 3)

    # ==== MOV direct,@R0/@R1 (0x86-0x87) ====
    _reg(0x86, "MOV direct,@R0", 2, ins.mov_direct_iR0, 2)
    _reg(0x87, "MOV direct,@R1", 2, ins.mov_direct_iR1, 2)

    # ==== MOV direct,R0-R7 (0x88-0x8F) ====
    for r in range(8):
        _reg(0x88 + r, f"MOV direct,R{r}", 2, ins.mov_direct_rn(r), 2)

    # ==== MOV DPTR,#imm16 (0x90) ====
    _reg(0x90, "MOV DPTR,#data16", 2, ins.mov_dptr_imm, 3)

    # ==== ACALL page4 (0x91-0x9F, odd) ====
    for i in range(8):
        _reg(0x91 + i*2, "ACALL", 2, ins.acall, 2)

    # ==== MOV bit,C (0x92) ====
    _reg(0x92, "MOV bit,C", 2, ins.mov_bit_c, 2)

    # ==== MOVC A,@A+DPTR (0x93) ====
    _reg(0x93, "MOVC A,@A+DPTR", 2, ins.movc_a_adptr)

    # ==== SUBB A,#imm (0x94) ====
    _reg(0x94, "SUBB A,#data", 1, ins.subb_a_imm, 2)

    # ==== SUBB A,direct (0x95) ====
    _reg(0x95, "SUBB A,direct", 1, ins.subb_a_direct, 2)

    # ==== SUBB A,@R0/@R1 (0x96-0x97) ====
    _reg(0x96, "SUBB A,@R0", 1, ins.subb_a_iR0)
    _reg(0x97, "SUBB A,@R1", 1, ins.subb_a_iR1)

    # ==== SUBB A,R0-R7 (0x98-0x9F) ====
    for r in range(8):
        _reg(0x98 + r, f"SUBB A,R{r}", 1, ins.subb_a_rn(r))

    # ==== ORL C,/bit (0xA0) ====
    _reg(0xA0, "ORL C,/bit", 2, ins.orl_c_nbit, 2)

    # ==== AJMP page5 (0xA1-0xBF, odd) ====
    for i in range(16):
        _reg(0xA1 + i*2, "AJMP", 2, ins.ajmp, 2)

    # ==== MOV C,bit (0xA2) ====
    _reg(0xA2, "MOV C,bit", 1, ins.mov_c_bit, 2)

    # ==== INC DPTR (0xA3) ====
    _reg(0xA3, "INC DPTR", 2, ins.inc_dptr)

    # ==== MUL AB (0xA4) ====
    _reg(0xA4, "MUL AB", 4, ins.mul_ab)

    # ==== (0xA5) reserved - NOP ====

    # ==== MOV @R0/@R1,direct (0xA6-0xA7) ====
    _reg(0xA6, "MOV @R0,direct", 2, ins.mov_iR0_direct, 2)
    _reg(0xA7, "MOV @R1,direct", 2, ins.mov_iR1_direct, 2)

    # ==== MOV R0-R7,direct (0xA8-0xAF) ====
    for r in range(8):
        _reg(0xA8 + r, f"MOV R{r},direct", 2, ins.mov_rn_direct(r), 2)

    # ==== ANL C,/bit (0xB0) ====
    _reg(0xB0, "ANL C,/bit", 2, ins.anl_c_nbit, 2)

    # ==== ACALL page5 (0xB1-0xBF, odd) ====
    for i in range(8):
        _reg(0xB1 + i*2, "ACALL", 2, ins.acall, 2)

    # ==== CPL bit (0xB2) ====
    _reg(0xB2, "CPL bit", 1, ins.cpl_bit, 2)

    # ==== CPL C (0xB3) ====
    _reg(0xB3, "CPL C", 1, ins.cpl_c)

    # ==== CJNE A,#imm,rel (0xB4) ====
    _reg(0xB4, "CJNE A,#data,rel", 2, ins.cjne_a_imm, 3)

    # ==== CJNE A,direct,rel (0xB5) ====
    _reg(0xB5, "CJNE A,direct,rel", 2, ins.cjne_a_direct, 3)

    # ==== CJNE @R0/@R1,#imm,rel (0xB6-0xB7) ====
    _reg(0xB6, "CJNE @R0,#data,rel", 2, ins.cjne_iR0_imm, 3)
    _reg(0xB7, "CJNE @R1,#data,rel", 2, ins.cjne_iR1_imm, 3)

    # ==== CJNE R0-R7,#imm,rel (0xB8-0xBF) ====
    for r in range(8):
        _reg(0xB8 + r, f"CJNE R{r},#data,rel", 2, ins.cjne_rn_imm(r), 3)

    # ==== PUSH direct (0xC0) ====
    _reg(0xC0, "PUSH direct", 2, ins.push_direct, 2)

    # ==== AJMP page6 (0xC1-0xDF, odd) ====
    for i in range(16):
        _reg(0xC1 + i*2, "AJMP", 2, ins.ajmp, 2)

    # ==== CLR bit (0xC2) ====
    _reg(0xC2, "CLR bit", 1, ins.clr_bit, 2)

    # ==== CLR C (0xC3) ====
    _reg(0xC3, "CLR C", 1, ins.clr_c)

    # ==== SWAP A (0xC4) ====
    _reg(0xC4, "SWAP A", 1, ins.swap_a)

    # ==== XCH A,direct (0xC5) ====
    _reg(0xC5, "XCH A,direct", 1, ins.xch_a_direct, 2)

    # ==== XCH A,@R0/@R1 (0xC6-0xC7) ====
    _reg(0xC6, "XCH A,@R0", 1, ins.xch_a_iR0)
    _reg(0xC7, "XCH A,@R1", 1, ins.xch_a_iR1)

    # ==== XCH A,R0-R7 (0xC8-0xCF) ====
    for r in range(8):
        _reg(0xC8 + r, f"XCH A,R{r}", 1, ins.xch_a_rn(r))

    # ==== POP direct (0xD0) ====
    _reg(0xD0, "POP direct", 2, ins.pop_direct, 2)

    # ==== ACALL page6 (0xD1-0xDF, odd) ====
    for i in range(8):
        _reg(0xD1 + i*2, "ACALL", 2, ins.acall, 2)

    # ==== SETB bit (0xD2) ====
    _reg(0xD2, "SETB bit", 1, ins.setb_bit, 2)

    # ==== SETB C (0xD3) ====
    _reg(0xD3, "SETB C", 1, ins.setb_c)

    # ==== DA A (0xD4) ====
    _reg(0xD4, "DA A", 1, ins.da_a)

    # ==== DJNZ direct,rel (0xD5) ====
    _reg(0xD5, "DJNZ direct,rel", 2, ins.djnz_direct, 3)

    # ==== XCHD A,@R0/@R1 (0xD6-0xD7) ====
    _reg(0xD6, "XCHD A,@R0", 1, ins.xchd_a_iR0)
    _reg(0xD7, "XCHD A,@R1", 1, ins.xchd_a_iR1)

    # ==== DJNZ R0-R7,rel (0xD8-0xDF) ====
    for r in range(8):
        _reg(0xD8 + r, f"DJNZ R{r},rel", 2, ins.djnz_rn(r), 2)

    # ==== MOVX A,@DPTR (0xE0) ====
    _reg(0xE0, "MOVX A,@DPTR", 2, ins.movx_a_dptr)

    # ==== AJMP page7 (0xE1-0xFF, odd) ====
    for i in range(16):
        _reg(0xE1 + i*2, "AJMP", 2, ins.ajmp, 2)

    # ==== MOVX A,@R0/@R1 (0xE2-0xE3) ====
    _reg(0xE2, "MOVX A,@R0", 2, ins.movx_a_iR0)
    _reg(0xE3, "MOVX A,@R1", 2, ins.movx_a_iR1)

    # ==== CLR A (0xE4) ====
    _reg(0xE4, "CLR A", 1, ins.clr_a)

    # ==== MOV A,direct (0xE5) ====
    _reg(0xE5, "MOV A,direct", 1, ins.mov_a_direct, 2)

    # ==== MOV A,@R0/@R1 (0xE6-0xE7) ====
    _reg(0xE6, "MOV A,@R0", 1, ins.mov_a_iR0)
    _reg(0xE7, "MOV A,@R1", 1, ins.mov_a_iR1)

    # ==== MOV A,R0-R7 (0xE8-0xEF) ====
    for r in range(8):
        _reg(0xE8 + r, f"MOV A,R{r}", 1, ins.mov_a_rn(r))

    # ==== MOVX @DPTR,A (0xF0) ====
    _reg(0xF0, "MOVX @DPTR,A", 2, ins.movx_dptr_a)

    # ==== ACALL page7 (0xF1-0xFF, odd) ====
    for i in range(8):
        _reg(0xF1 + i*2, "ACALL", 2, ins.acall, 2)

    # ==== MOVX @R0/@R1,A (0xF2-0xF3) ====
    _reg(0xF2, "MOVX @R0,A", 2, ins.movx_iR0_a)
    _reg(0xF3, "MOVX @R1,A", 2, ins.movx_iR1_a)

    # ==== CPL A (0xF4) ====
    _reg(0xF4, "CPL A", 1, ins.cpl_a)

    # ==== MOV direct,A (0xF5) ====
    _reg(0xF5, "MOV direct,A", 1, ins.mov_direct_a, 2)

    # ==== MOV @R0/@R1,A (0xF6-0xF7) ====
    _reg(0xF6, "MOV @R0,A", 1, ins.mov_iR0_a)
    _reg(0xF7, "MOV @R1,A", 1, ins.mov_iR1_a)

    # ==== MOV R0-R7,A (0xF8-0xFF) ====
    for r in range(8):
        _reg(0xF8 + r, f"MOV R{r},A", 1, ins.mov_rn_a(r))

    # Fill remaining undefined slots with NOP-equivalent
    for op in range(256):
        if op not in OPCODES:
            _reg(op, f"NOP_{op:02X}", 1, ins.nop)


def decode(opcode: int) -> InstrInfo:
    """Decode an opcode, returning InstrInfo (or invalid placeholder)."""
    return OPCODES.get(opcode, InstrInfo.invalid(opcode))
