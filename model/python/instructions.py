"""8051 Instruction implementations. Each handler takes (cpu, opcode) and executes one instruction."""

from .memory import (SFR_ACC, SFR_PSW, SFR_SP, SFR_DPH, SFR_DPL,
                      PSW_CY, PSW_AC, PSW_OV, PSW_P, PSW_RS0, PSW_RS1)
from .alu import ALU


def _signed_rel(imm: int) -> int:
    """Convert 8-bit signed relative offset to PC delta."""
    if imm & 0x80:
        return imm - 256
    return imm


# ===== NOP =====
def nop(cpu, opcode: int) -> None:
    pass


# ===== MOV =====
def mov_a_imm(cpu, opcode: int) -> None:
    cpu.mem.acc = cpu.fetch()

def mov_a_direct(cpu, opcode: int) -> None:
    cpu.mem.acc = cpu.mem.read_iram(cpu.fetch())

def mov_a_iR0(cpu, opcode: int) -> None:
    cpu.mem.acc = cpu.mem.read_iram(cpu.mem.read_iram(cpu.r0_addr()))

def mov_a_iR1(cpu, opcode: int) -> None:
    cpu.mem.acc = cpu.mem.read_iram(cpu.mem.read_iram(cpu.r1_addr()))

def mov_a_rn(r: int):
    def handler(cpu, opcode: int) -> None:
        cpu.mem.acc = cpu.read_rn(r)
    return handler

def mov_direct_a(cpu, opcode: int) -> None:
    cpu.mem.write_iram(cpu.fetch(), cpu.mem.acc)

def mov_direct_imm(cpu, opcode: int) -> None:
    addr = cpu.fetch()
    cpu.mem.write_iram(addr, cpu.fetch())

def mov_direct_direct(cpu, opcode: int) -> None:
    dst = cpu.fetch()
    src = cpu.fetch()
    cpu.mem.write_iram(dst, cpu.mem.read_iram(src))

def mov_direct_iR0(cpu, opcode: int) -> None:
    cpu.mem.write_iram(cpu.fetch(), cpu.mem.read_iram(cpu.r0_addr()))

def mov_direct_iR1(cpu, opcode: int) -> None:
    cpu.mem.write_iram(cpu.fetch(), cpu.mem.read_iram(cpu.r1_addr()))

def mov_direct_rn(r: int):
    def handler(cpu, opcode: int) -> None:
        cpu.mem.write_iram(cpu.fetch(), cpu.read_rn(r))
    return handler

def mov_rn_a(r: int):
    def handler(cpu, opcode: int) -> None:
        cpu.write_rn(r, cpu.mem.acc)
    return handler

def mov_rn_imm(r: int):
    def handler(cpu, opcode: int) -> None:
        cpu.write_rn(r, cpu.fetch())
    return handler

def mov_rn_direct(r: int):
    def handler(cpu, opcode: int) -> None:
        cpu.write_rn(r, cpu.mem.read_iram(cpu.fetch()))
    return handler

def mov_iR0_a(cpu, opcode: int) -> None:
    cpu.mem.write_iram(cpu.r0_addr(), cpu.mem.acc)

def mov_iR1_a(cpu, opcode: int) -> None:
    cpu.mem.write_iram(cpu.r1_addr(), cpu.mem.acc)

def mov_iR0_imm(cpu, opcode: int) -> None:
    cpu.mem.write_iram(cpu.r0_addr(), cpu.fetch())

def mov_iR1_imm(cpu, opcode: int) -> None:
    cpu.mem.write_iram(cpu.r1_addr(), cpu.fetch())

def mov_iR0_direct(cpu, opcode: int) -> None:
    cpu.mem.write_iram(cpu.r0_addr(), cpu.mem.read_iram(cpu.fetch()))

def mov_iR1_direct(cpu, opcode: int) -> None:
    cpu.mem.write_iram(cpu.r1_addr(), cpu.mem.read_iram(cpu.fetch()))

def mov_dptr_imm(cpu, opcode: int) -> None:
    dph_val = cpu.fetch()
    dpl_val = cpu.fetch()
    cpu.mem.dptr = (dph_val << 8) | dpl_val


# ===== MOVC =====
def movc_a_apc(cpu, opcode: int) -> None:
    addr = cpu.pc + cpu.mem.acc
    cpu.mem.acc = cpu.mem.read_rom(addr & 0xFFFF)

def movc_a_adptr(cpu, opcode: int) -> None:
    addr = cpu.mem.dptr + cpu.mem.acc
    cpu.mem.acc = cpu.mem.read_rom(addr & 0xFFFF)


# ===== MOVX =====
def movx_a_dptr(cpu, opcode: int) -> None:
    cpu.mem.acc = cpu.mem.read_xram(cpu.mem.dptr)

def movx_a_iR0(cpu, opcode: int) -> None:
    addr = cpu.mem.read_iram(cpu.r0_addr())
    cpu.mem.acc = cpu.mem.read_xram(addr)

def movx_a_iR1(cpu, opcode: int) -> None:
    addr = cpu.mem.read_iram(cpu.r1_addr())
    cpu.mem.acc = cpu.mem.read_xram(addr)

def movx_dptr_a(cpu, opcode: int) -> None:
    cpu.mem.write_xram(cpu.mem.dptr, cpu.mem.acc)

def movx_iR0_a(cpu, opcode: int) -> None:
    addr = cpu.mem.read_iram(cpu.r0_addr())
    cpu.mem.write_xram(addr, cpu.mem.acc)

def movx_iR1_a(cpu, opcode: int) -> None:
    addr = cpu.mem.read_iram(cpu.r1_addr())
    cpu.mem.write_xram(addr, cpu.mem.acc)


# ===== PUSH / POP =====
def push_direct(cpu, opcode: int) -> None:
    val = cpu.mem.read_iram(cpu.fetch())
    new_sp = (cpu.mem.sp + 1) & 0xFF
    cpu.mem.sp = new_sp
    cpu.mem.write_iram(new_sp, val)

def pop_direct(cpu, opcode: int) -> None:
    val = cpu.mem.read_iram(cpu.mem.sp)
    cpu.mem.sp = (cpu.mem.sp - 1) & 0xFF
    cpu.mem.write_iram(cpu.fetch(), val)


# ===== XCH / XCHD / SWAP =====
def xch_a_direct(cpu, opcode: int) -> None:
    addr = cpu.fetch()
    tmp = cpu.mem.read_iram(addr)
    cpu.mem.write_iram(addr, cpu.mem.acc)
    cpu.mem.acc = tmp

def xch_a_iR0(cpu, opcode: int) -> None:
    addr = cpu.r0_addr()
    tmp = cpu.mem.read_iram(addr)
    cpu.mem.write_iram(addr, cpu.mem.acc)
    cpu.mem.acc = tmp

def xch_a_iR1(cpu, opcode: int) -> None:
    addr = cpu.r1_addr()
    tmp = cpu.mem.read_iram(addr)
    cpu.mem.write_iram(addr, cpu.mem.acc)
    cpu.mem.acc = tmp

def xch_a_rn(r: int):
    def handler(cpu, opcode: int) -> None:
        tmp = cpu.read_rn(r)
        cpu.write_rn(r, cpu.mem.acc)
        cpu.mem.acc = tmp
    return handler

def xchd_a_iR0(cpu, opcode: int) -> None:
    addr = cpu.r0_addr()
    v = cpu.mem.read_iram(addr)
    a = cpu.mem.acc
    cpu.mem.acc = (a & 0xF0) | (v & 0x0F)
    cpu.mem.write_iram(addr, (v & 0xF0) | (a & 0x0F))

def xchd_a_iR1(cpu, opcode: int) -> None:
    addr = cpu.r1_addr()
    v = cpu.mem.read_iram(addr)
    a = cpu.mem.acc
    cpu.mem.acc = (a & 0xF0) | (v & 0x0F)
    cpu.mem.write_iram(addr, (v & 0xF0) | (a & 0x0F))

def swap_a(cpu, opcode: int) -> None:
    cpu.mem.acc = ALU.swap(cpu.mem.acc)


# ===== ADD =====
def add_a_imm(cpu, opcode: int) -> None:
    v, psw = ALU.add(cpu.mem.acc, cpu.fetch(), cpu.mem.psw)
    cpu.mem.acc = v; cpu.mem.psw = psw

def add_a_direct(cpu, opcode: int) -> None:
    v, psw = ALU.add(cpu.mem.acc, cpu.mem.read_iram(cpu.fetch()), cpu.mem.psw)
    cpu.mem.acc = v; cpu.mem.psw = psw

def add_a_iR0(cpu, opcode: int) -> None:
    v, psw = ALU.add(cpu.mem.acc, cpu.mem.read_iram(cpu.r0_addr()), cpu.mem.psw)
    cpu.mem.acc = v; cpu.mem.psw = psw

def add_a_iR1(cpu, opcode: int) -> None:
    v, psw = ALU.add(cpu.mem.acc, cpu.mem.read_iram(cpu.r1_addr()), cpu.mem.psw)
    cpu.mem.acc = v; cpu.mem.psw = psw

def add_a_rn(r: int):
    def handler(cpu, opcode: int) -> None:
        v, psw = ALU.add(cpu.mem.acc, cpu.read_rn(r), cpu.mem.psw)
        cpu.mem.acc = v; cpu.mem.psw = psw
    return handler


# ===== ADDC =====
def addc_a_imm(cpu, opcode: int) -> None:
    v, psw = ALU.addc(cpu.mem.acc, cpu.fetch(), cpu.mem.psw)
    cpu.mem.acc = v; cpu.mem.psw = psw

def addc_a_direct(cpu, opcode: int) -> None:
    v, psw = ALU.addc(cpu.mem.acc, cpu.mem.read_iram(cpu.fetch()), cpu.mem.psw)
    cpu.mem.acc = v; cpu.mem.psw = psw

def addc_a_iR0(cpu, opcode: int) -> None:
    v, psw = ALU.addc(cpu.mem.acc, cpu.mem.read_iram(cpu.r0_addr()), cpu.mem.psw)
    cpu.mem.acc = v; cpu.mem.psw = psw

def addc_a_iR1(cpu, opcode: int) -> None:
    v, psw = ALU.addc(cpu.mem.acc, cpu.mem.read_iram(cpu.r1_addr()), cpu.mem.psw)
    cpu.mem.acc = v; cpu.mem.psw = psw

def addc_a_rn(r: int):
    def handler(cpu, opcode: int) -> None:
        v, psw = ALU.addc(cpu.mem.acc, cpu.read_rn(r), cpu.mem.psw)
        cpu.mem.acc = v; cpu.mem.psw = psw
    return handler


# ===== SUBB =====
def subb_a_imm(cpu, opcode: int) -> None:
    v, psw = ALU.subb(cpu.mem.acc, cpu.fetch(), cpu.mem.psw)
    cpu.mem.acc = v; cpu.mem.psw = psw

def subb_a_direct(cpu, opcode: int) -> None:
    v, psw = ALU.subb(cpu.mem.acc, cpu.mem.read_iram(cpu.fetch()), cpu.mem.psw)
    cpu.mem.acc = v; cpu.mem.psw = psw

def subb_a_iR0(cpu, opcode: int) -> None:
    v, psw = ALU.subb(cpu.mem.acc, cpu.mem.read_iram(cpu.r0_addr()), cpu.mem.psw)
    cpu.mem.acc = v; cpu.mem.psw = psw

def subb_a_iR1(cpu, opcode: int) -> None:
    v, psw = ALU.subb(cpu.mem.acc, cpu.mem.read_iram(cpu.r1_addr()), cpu.mem.psw)
    cpu.mem.acc = v; cpu.mem.psw = psw

def subb_a_rn(r: int):
    def handler(cpu, opcode: int) -> None:
        v, psw = ALU.subb(cpu.mem.acc, cpu.read_rn(r), cpu.mem.psw)
        cpu.mem.acc = v; cpu.mem.psw = psw
    return handler


# ===== INC =====
def inc_a(cpu, opcode: int) -> None:
    cpu.mem.acc = ALU.inc(cpu.mem.acc)

def inc_direct(cpu, opcode: int) -> None:
    addr = cpu.fetch()
    cpu.mem.write_iram(addr, ALU.inc(cpu.mem.read_iram(addr)))

def inc_iR0(cpu, opcode: int) -> None:
    addr = cpu.r0_addr()
    cpu.mem.write_iram(addr, ALU.inc(cpu.mem.read_iram(addr)))

def inc_iR1(cpu, opcode: int) -> None:
    addr = cpu.r1_addr()
    cpu.mem.write_iram(addr, ALU.inc(cpu.mem.read_iram(addr)))

def inc_rn(r: int):
    def handler(cpu, opcode: int) -> None:
        cpu.write_rn(r, ALU.inc(cpu.read_rn(r)))
    return handler

def inc_dptr(cpu, opcode: int) -> None:
    cpu.mem.dptr = (cpu.mem.dptr + 1) & 0xFFFF


# ===== DEC =====
def dec_a(cpu, opcode: int) -> None:
    cpu.mem.acc = ALU.dec(cpu.mem.acc)

def dec_direct(cpu, opcode: int) -> None:
    addr = cpu.fetch()
    cpu.mem.write_iram(addr, ALU.dec(cpu.mem.read_iram(addr)))

def dec_iR0(cpu, opcode: int) -> None:
    addr = cpu.r0_addr()
    cpu.mem.write_iram(addr, ALU.dec(cpu.mem.read_iram(addr)))

def dec_iR1(cpu, opcode: int) -> None:
    addr = cpu.r1_addr()
    cpu.mem.write_iram(addr, ALU.dec(cpu.mem.read_iram(addr)))

def dec_rn(r: int):
    def handler(cpu, opcode: int) -> None:
        cpu.write_rn(r, ALU.dec(cpu.read_rn(r)))
    return handler


# ===== MUL / DIV =====
def mul_ab(cpu, opcode: int) -> None:
    a, b_val, psw = ALU.mul(cpu.mem.acc, cpu.mem.b, cpu.mem.psw)
    cpu.mem.acc = a; cpu.mem.b = b_val; cpu.mem.psw = psw

def div_ab(cpu, opcode: int) -> None:
    a, b_val, psw = ALU.div(cpu.mem.acc, cpu.mem.b, cpu.mem.psw)
    cpu.mem.acc = a; cpu.mem.b = b_val; cpu.mem.psw = psw

def da_a(cpu, opcode: int) -> None:
    v, psw = ALU.da(cpu.mem.acc, cpu.mem.psw)
    cpu.mem.acc = v; cpu.mem.psw = psw


# ===== ANL =====
def anl_a_imm(cpu, opcode: int) -> None:
    cpu.mem.acc = ALU.anl(cpu.mem.acc, cpu.fetch())

def anl_a_direct(cpu, opcode: int) -> None:
    cpu.mem.acc = ALU.anl(cpu.mem.acc, cpu.mem.read_iram(cpu.fetch()))

def anl_a_iR0(cpu, opcode: int) -> None:
    cpu.mem.acc = ALU.anl(cpu.mem.acc, cpu.mem.read_iram(cpu.r0_addr()))

def anl_a_iR1(cpu, opcode: int) -> None:
    cpu.mem.acc = ALU.anl(cpu.mem.acc, cpu.mem.read_iram(cpu.r1_addr()))

def anl_a_rn(r: int):
    def handler(cpu, opcode: int) -> None:
        cpu.mem.acc = ALU.anl(cpu.mem.acc, cpu.read_rn(r))
    return handler

def anl_direct_a(cpu, opcode: int) -> None:
    addr = cpu.fetch()
    cpu.mem.write_iram(addr, ALU.anl(cpu.mem.read_iram(addr), cpu.mem.acc))

def anl_direct_imm(cpu, opcode: int) -> None:
    addr = cpu.fetch()
    cpu.mem.write_iram(addr, ALU.anl(cpu.mem.read_iram(addr), cpu.fetch()))


# ===== ORL =====
def orl_a_imm(cpu, opcode: int) -> None:
    cpu.mem.acc = ALU.orl(cpu.mem.acc, cpu.fetch())

def orl_a_direct(cpu, opcode: int) -> None:
    cpu.mem.acc = ALU.orl(cpu.mem.acc, cpu.mem.read_iram(cpu.fetch()))

def orl_a_iR0(cpu, opcode: int) -> None:
    cpu.mem.acc = ALU.orl(cpu.mem.acc, cpu.mem.read_iram(cpu.r0_addr()))

def orl_a_iR1(cpu, opcode: int) -> None:
    cpu.mem.acc = ALU.orl(cpu.mem.acc, cpu.mem.read_iram(cpu.r1_addr()))

def orl_a_rn(r: int):
    def handler(cpu, opcode: int) -> None:
        cpu.mem.acc = ALU.orl(cpu.mem.acc, cpu.read_rn(r))
    return handler

def orl_direct_a(cpu, opcode: int) -> None:
    addr = cpu.fetch()
    cpu.mem.write_iram(addr, ALU.orl(cpu.mem.read_iram(addr), cpu.mem.acc))

def orl_direct_imm(cpu, opcode: int) -> None:
    addr = cpu.fetch()
    cpu.mem.write_iram(addr, ALU.orl(cpu.mem.read_iram(addr), cpu.fetch()))


# ===== XRL =====
def xrl_a_imm(cpu, opcode: int) -> None:
    cpu.mem.acc = ALU.xrl(cpu.mem.acc, cpu.fetch())

def xrl_a_direct(cpu, opcode: int) -> None:
    cpu.mem.acc = ALU.xrl(cpu.mem.acc, cpu.mem.read_iram(cpu.fetch()))

def xrl_a_iR0(cpu, opcode: int) -> None:
    cpu.mem.acc = ALU.xrl(cpu.mem.acc, cpu.mem.read_iram(cpu.r0_addr()))

def xrl_a_iR1(cpu, opcode: int) -> None:
    cpu.mem.acc = ALU.xrl(cpu.mem.acc, cpu.mem.read_iram(cpu.r1_addr()))

def xrl_a_rn(r: int):
    def handler(cpu, opcode: int) -> None:
        cpu.mem.acc = ALU.xrl(cpu.mem.acc, cpu.read_rn(r))
    return handler

def xrl_direct_a(cpu, opcode: int) -> None:
    addr = cpu.fetch()
    cpu.mem.write_iram(addr, ALU.xrl(cpu.mem.read_iram(addr), cpu.mem.acc))

def xrl_direct_imm(cpu, opcode: int) -> None:
    addr = cpu.fetch()
    cpu.mem.write_iram(addr, ALU.xrl(cpu.mem.read_iram(addr), cpu.fetch()))


# ===== CLR / CPL =====
def clr_a(cpu, opcode: int) -> None:
    cpu.mem.acc = 0

def cpl_a(cpu, opcode: int) -> None:
    cpu.mem.acc = ALU.cpl(cpu.mem.acc)


# ===== Rotate =====
def rl_a(cpu, opcode: int) -> None:
    cpu.mem.acc = ALU.rl(cpu.mem.acc)

def rlc_a(cpu, opcode: int) -> None:
    v, psw = ALU.rlc(cpu.mem.acc, cpu.mem.psw)
    cpu.mem.acc = v; cpu.mem.psw = psw

def rr_a(cpu, opcode: int) -> None:
    cpu.mem.acc = ALU.rr(cpu.mem.acc)

def rrc_a(cpu, opcode: int) -> None:
    v, psw = ALU.rrc(cpu.mem.acc, cpu.mem.psw)
    cpu.mem.acc = v; cpu.mem.psw = psw


# ===== Bit operations =====
def clr_c(cpu, opcode: int) -> None:
    cpu.mem.write_carry(False)

def setb_c(cpu, opcode: int) -> None:
    cpu.mem.write_carry(True)

def cpl_c(cpu, opcode: int) -> None:
    cpu.mem.write_carry(not cpu.mem.read_carry())

def clr_bit(cpu, opcode: int) -> None:
    cpu.mem.write_bit(cpu.fetch(), False)

def setb_bit(cpu, opcode: int) -> None:
    cpu.mem.write_bit(cpu.fetch(), True)

def cpl_bit(cpu, opcode: int) -> None:
    addr = cpu.fetch()
    cpu.mem.write_bit(addr, not cpu.mem.read_bit(addr))

def mov_c_bit(cpu, opcode: int) -> None:
    cpu.mem.write_carry(cpu.mem.read_bit(cpu.fetch()))

def mov_bit_c(cpu, opcode: int) -> None:
    cpu.mem.write_bit(cpu.fetch(), cpu.mem.read_carry())

def anl_c_bit(cpu, opcode: int) -> None:
    v = cpu.mem.read_carry() and cpu.mem.read_bit(cpu.fetch())
    cpu.mem.write_carry(v)

def anl_c_nbit(cpu, opcode: int) -> None:
    v = cpu.mem.read_carry() and (not cpu.mem.read_bit(cpu.fetch()))
    cpu.mem.write_carry(v)

def orl_c_bit(cpu, opcode: int) -> None:
    v = cpu.mem.read_carry() or cpu.mem.read_bit(cpu.fetch())
    cpu.mem.write_carry(v)

def orl_c_nbit(cpu, opcode: int) -> None:
    v = cpu.mem.read_carry() or (not cpu.mem.read_bit(cpu.fetch()))
    cpu.mem.write_carry(v)


# ===== Jumps =====
def ajmp(cpu, opcode: int) -> None:
    """AJMP addr11: opcode[7:5]=page, byte2=addr_low. PC = (PC+2 & 0xF800) | addr11"""
    addr = cpu.fetch()
    target = ((cpu.pc & 0xF800) | ((opcode & 0xE0) << 3) | addr)
    cpu.pc = target & 0xFFFF

def ljmp(cpu, opcode: int) -> None:
    high = cpu.fetch()
    low = cpu.fetch()
    cpu.pc = ((high << 8) | low) & 0xFFFF

def sjmp(cpu, opcode: int) -> None:
    rel = _signed_rel(cpu.fetch())
    cpu.pc = (cpu.pc + rel) & 0xFFFF

def jmp_adptr(cpu, opcode: int) -> None:
    cpu.pc = (cpu.mem.dptr + cpu.mem.acc) & 0xFFFF

def jz(cpu, opcode: int) -> None:
    rel = _signed_rel(cpu.fetch())
    if cpu.mem.acc == 0:
        cpu.pc = (cpu.pc + rel) & 0xFFFF

def jnz(cpu, opcode: int) -> None:
    rel = _signed_rel(cpu.fetch())
    if cpu.mem.acc != 0:
        cpu.pc = (cpu.pc + rel) & 0xFFFF

def jc(cpu, opcode: int) -> None:
    rel = _signed_rel(cpu.fetch())
    if cpu.mem.read_carry():
        cpu.pc = (cpu.pc + rel) & 0xFFFF

def jnc(cpu, opcode: int) -> None:
    rel = _signed_rel(cpu.fetch())
    if not cpu.mem.read_carry():
        cpu.pc = (cpu.pc + rel) & 0xFFFF

def jb(cpu, opcode: int) -> None:
    bit_addr = cpu.fetch()
    rel = _signed_rel(cpu.fetch())
    if cpu.mem.read_bit(bit_addr):
        cpu.pc = (cpu.pc + rel) & 0xFFFF

def jnb(cpu, opcode: int) -> None:
    bit_addr = cpu.fetch()
    rel = _signed_rel(cpu.fetch())
    if not cpu.mem.read_bit(bit_addr):
        cpu.pc = (cpu.pc + rel) & 0xFFFF

def jbc(cpu, opcode: int) -> None:
    bit_addr = cpu.fetch()
    rel = _signed_rel(cpu.fetch())
    if cpu.mem.read_bit(bit_addr):
        cpu.mem.write_bit(bit_addr, False)
        cpu.pc = (cpu.pc + rel) & 0xFFFF


# ===== CJNE / DJNZ =====
def cjne_a_imm(cpu, opcode: int) -> None:
    imm = cpu.fetch()
    rel = _signed_rel(cpu.fetch())
    if cpu.mem.acc != imm:
        cpu.pc = (cpu.pc + rel) & 0xFFFF
    # Set CY if A < imm
    cpu.mem.write_carry(cpu.mem.acc < imm)

def cjne_a_direct(cpu, opcode: int) -> None:
    addr = cpu.fetch()
    rel = _signed_rel(cpu.fetch())
    v = cpu.mem.read_iram(addr)
    if cpu.mem.acc != v:
        cpu.pc = (cpu.pc + rel) & 0xFFFF
    cpu.mem.write_carry(cpu.mem.acc < v)

def cjne_iR0_imm(cpu, opcode: int) -> None:
    imm = cpu.fetch()
    rel = _signed_rel(cpu.fetch())
    v = cpu.mem.read_iram(cpu.r0_addr())
    if v != imm:
        cpu.pc = (cpu.pc + rel) & 0xFFFF
    cpu.mem.write_carry(v < imm)

def cjne_iR1_imm(cpu, opcode: int) -> None:
    imm = cpu.fetch()
    rel = _signed_rel(cpu.fetch())
    v = cpu.mem.read_iram(cpu.r1_addr())
    if v != imm:
        cpu.pc = (cpu.pc + rel) & 0xFFFF
    cpu.mem.write_carry(v < imm)

def cjne_rn_imm(r: int):
    def handler(cpu, opcode: int) -> None:
        imm = cpu.fetch()
        rel = _signed_rel(cpu.fetch())
        v = cpu.read_rn(r)
        if v != imm:
            cpu.pc = (cpu.pc + rel) & 0xFFFF
        cpu.mem.write_carry(v < imm)
    return handler

def djnz_direct(cpu, opcode: int) -> None:
    addr = cpu.fetch()
    rel = _signed_rel(cpu.fetch())
    v = ALU.dec(cpu.mem.read_iram(addr))
    cpu.mem.write_iram(addr, v)
    if v != 0:
        cpu.pc = (cpu.pc + rel) & 0xFFFF

def djnz_rn(r: int):
    def handler(cpu, opcode: int) -> None:
        rel = _signed_rel(cpu.fetch())
        v = ALU.dec(cpu.read_rn(r))
        cpu.write_rn(r, v)
        if v != 0:
            cpu.pc = (cpu.pc + rel) & 0xFFFF
    return handler


# ===== CALL / RET =====
def acall(cpu, opcode: int) -> None:
    """ACALL addr11: push PC, jump to addr11."""
    addr = cpu.fetch()
    ret_addr = cpu.pc  # PC already at next instruction
    # Push return address (little-endian)
    sp = cpu.mem.sp
    cpu.mem.write_iram((sp + 1) & 0xFF, ret_addr & 0xFF)
    cpu.mem.write_iram((sp + 2) & 0xFF, (ret_addr >> 8) & 0xFF)
    cpu.mem.sp = (sp + 2) & 0xFF
    target = ((cpu.pc & 0xF800) | ((opcode & 0xE0) << 3) | addr)
    cpu.pc = target & 0xFFFF

def lcall(cpu, opcode: int) -> None:
    high = cpu.fetch()
    low = cpu.fetch()
    ret_addr = cpu.pc
    sp = cpu.mem.sp
    cpu.mem.write_iram((sp + 1) & 0xFF, ret_addr & 0xFF)
    cpu.mem.write_iram((sp + 2) & 0xFF, (ret_addr >> 8) & 0xFF)
    cpu.mem.sp = (sp + 2) & 0xFF
    cpu.pc = ((high << 8) | low) & 0xFFFF

def ret(cpu, opcode: int) -> None:
    sp = cpu.mem.sp
    high = cpu.mem.read_iram(sp)
    low = cpu.mem.read_iram((sp - 1) & 0xFF)
    cpu.mem.sp = (sp - 2) & 0xFF
    cpu.pc = ((high << 8) | low) & 0xFFFF

def reti(cpu, opcode: int) -> None:
    # Same as RET but also signals interrupt return
    ret(cpu, opcode)
    cpu.interrupt_active = False
